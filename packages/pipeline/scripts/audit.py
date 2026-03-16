"""CLI entry point: completeness audit — verify scraped data in PostgreSQL."""

from __future__ import annotations

import argparse
import os

import psycopg2
from rich.console import Console
from rich.table import Table

console = Console()

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:54321/postgres"


AUDIT_QUERY = """\
SELECT
    s.abbreviation,
    s.gender,
    s.name,
    COUNT(DISTINCT g.game_id)     AS total_games,
    COUNT(DISTINCT g.season_year) AS seasons,
    MIN(g.season_year)            AS first_season,
    MAX(g.season_year)            AS last_season
FROM schools s
LEFT JOIN games g ON g.school_id = s.id
WHERE s.enabled = true
GROUP BY s.id, s.abbreviation, s.gender, s.name
ORDER BY s.gender, s.abbreviation;
"""

TOTALS_QUERY = """\
SELECT
    (SELECT COUNT(*) FROM games)              AS total_games,
    (SELECT COUNT(*) FROM player_game_stats)  AS total_player_stats,
    (SELECT COUNT(*) FROM team_game_stats)    AS total_team_stats,
    (SELECT COUNT(*) FROM game_events)        AS total_events;
"""

CONFERENCE_QUERY = """\
SELECT
    COUNT(*) FILTER (WHERE home_conference IS NOT NULL) AS has_conf,
    COUNT(*) FILTER (WHERE home_conference IS NULL)     AS missing_conf,
    COUNT(*)                                            AS total
FROM games;
"""


def main() -> None:
    """Entry point for ``uv run audit``."""
    parser = argparse.ArgumentParser(description="Completeness audit of scraped data")
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="PostgreSQL connection URL",
    )
    args = parser.parse_args()

    database_url = args.database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    # Per-school breakdown
    cur.execute(AUDIT_QUERY)
    rows = cur.fetchall()

    table = Table(title="GAC Program Completeness Audit")
    table.add_column("Abbrev", style="cyan")
    table.add_column("Gender")
    table.add_column("School")
    table.add_column("Games", justify="right")
    table.add_column("Seasons", justify="right")
    table.add_column("First", justify="right")
    table.add_column("Last", justify="right")
    table.add_column("Status", justify="center")

    zero_schools = []
    for row in rows:
        abbrev, gender, name, games, seasons, first, last = row
        status = "[green]OK" if games > 0 else "[red]EMPTY"
        if games == 0:
            zero_schools.append(abbrev)
        table.add_row(
            abbrev, gender, name,
            str(games), str(seasons or 0),
            str(first or "-"), str(last or "-"),
            status,
        )

    console.print(table)

    # Totals
    cur.execute(TOTALS_QUERY)
    totals = cur.fetchone()
    console.print(f"\n[bold]Total games:[/bold] {totals[0]}")
    console.print(f"[bold]Total player stats:[/bold] {totals[1]}")
    console.print(f"[bold]Total team stats:[/bold] {totals[2]}")
    console.print(f"[bold]Total events:[/bold] {totals[3]}")

    # Conference coverage
    cur.execute(CONFERENCE_QUERY)
    conf = cur.fetchone()
    console.print(
        f"\n[bold]Conference coverage:[/bold] "
        f"{conf[0]}/{conf[2]} games have home_conference set"
    )

    # Acceptance checks
    console.print("\n[bold]Acceptance Checks:[/bold]")
    game_count = totals[0]
    passed = True

    if game_count >= 1500:
        console.print(f"  [green]PASS  games > 1,500 ({game_count})")
    else:
        console.print(f"  [red]FAIL  games > 1,500 ({game_count})")
        passed = False

    if zero_schools:
        console.print(f"  [red]FAIL  schools with 0 games: {', '.join(zero_schools)}")
        passed = False
    else:
        console.print(f"  [green]PASS  all {len(rows)} schools have games")

    if conf[1] == 0:
        console.print("  [green]PASS  all games have home_conference")
    else:
        console.print(f"  [yellow]WARN  {conf[1]} games missing home_conference")

    if passed:
        console.print("\n[bold green]All acceptance criteria met.")
    else:
        console.print("\n[bold red]Some acceptance criteria not met.")

    conn.close()


if __name__ == "__main__":
    main()
