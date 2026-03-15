"""CLI entry point: load parquet data from data/structured/ into PostgreSQL."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2
from rich.console import Console
from rich.table import Table

console = Console()

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:54321/postgres"
STRUCTURED_DIR = Path("data/structured")


def _get_connection(database_url: str) -> psycopg2.extensions.connection:
    """Connect to PostgreSQL."""
    return psycopg2.connect(database_url)


def _school_dirs(base: Path, school_filter: str | None) -> list[Path]:
    """Return school directories under data/structured/, optionally filtered."""
    if not base.exists():
        return []
    dirs = sorted(
        d for d in base.iterdir()
        if d.is_dir() and d.name != "all"
    )
    if school_filter:
        dirs = [d for d in dirs if d.name.upper() == school_filter.upper()]
    return dirs


def _ensure_school(
    cur: psycopg2.extensions.cursor,
    abbrev: str,
) -> int:
    """Upsert school from config and return its id."""
    from src.config import load_schools

    schools = load_schools()
    config = next((s for s in schools if s.abbreviation.upper() == abbrev.upper()), None)

    if config:
        cur.execute(
            """
            INSERT INTO schools (name, abbreviation, conference, mascot)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (abbreviation) DO UPDATE
                SET name = EXCLUDED.name,
                    conference = EXCLUDED.conference,
                    mascot = EXCLUDED.mascot
            RETURNING id
            """,
            (config.name, config.abbreviation, config.conference, config.mascot),
        )
    else:
        # No config entry — insert minimal record
        cur.execute(
            """
            INSERT INTO schools (name, abbreviation)
            VALUES (%s, %s)
            ON CONFLICT (abbreviation) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (abbrev.upper(), abbrev.upper()),
        )
    return cur.fetchone()[0]


def _date_or_none(val) -> str | None:
    """Return val if it looks like a date string, else None."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    if not s or s.lower() in ("unknown", "nan", "none", "nat"):
        return None
    return s


def _load_games(
    cur: psycopg2.extensions.cursor,
    df: pd.DataFrame,
    school_id: int,
) -> int:
    """Upsert games. Returns number of rows upserted."""
    if df.empty:
        return 0

    count = 0
    for _, row in df.iterrows():
        cur.execute(
            """
            INSERT INTO games (game_id, school_id, season_year, source_url,
                               date, venue, attendance, home_team, away_team,
                               home_score, away_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (game_id) DO UPDATE
                SET school_id   = EXCLUDED.school_id,
                    season_year = EXCLUDED.season_year,
                    source_url  = EXCLUDED.source_url,
                    date        = EXCLUDED.date,
                    venue       = EXCLUDED.venue,
                    attendance  = EXCLUDED.attendance,
                    home_team   = EXCLUDED.home_team,
                    away_team   = EXCLUDED.away_team,
                    home_score  = EXCLUDED.home_score,
                    away_score  = EXCLUDED.away_score
            """,
            (
                int(row["game_id"]),
                school_id,
                int(row["season_year"]),
                row.get("source_url"),
                _date_or_none(row.get("date")),
                row.get("venue"),
                _int_or_none(row.get("attendance")),
                row.get("home_team"),
                row.get("away_team"),
                _int_or_none(row.get("home_score")),
                _int_or_none(row.get("away_score")),
            ),
        )
        count += 1
    return count


def _int_or_none(val) -> int | None:
    """Convert to int, returning None for NaN/None."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return int(val)


def _bool_or_none(val) -> bool | None:
    """Convert to bool, returning None for NaN/None."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return bool(val)


def _load_child_table(
    cur: psycopg2.extensions.cursor,
    table: str,
    df: pd.DataFrame,
    school_id: int,
    columns: list[str],
    row_builder,
) -> int:
    """Delete-and-insert rows for a child table, grouped by game_id. Returns count."""
    if df.empty:
        return 0

    game_ids = df["game_id"].unique().tolist()

    # Delete existing rows for these game_ids + school_id
    cur.execute(
        f"DELETE FROM {table} WHERE school_id = %s AND game_id = ANY(%s)",  # noqa: S608
        (school_id, game_ids),
    )

    count = 0
    for _, row in df.iterrows():
        values = row_builder(row, school_id)
        placeholders = ", ".join(["%s"] * len(columns))
        col_list = ", ".join(columns)
        cur.execute(
            f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})",  # noqa: S608
            values,
        )
        count += 1
    return count


def _team_stats_row(row: pd.Series, school_id: int) -> tuple:
    return (
        int(row["game_id"]),
        school_id,
        row.get("team"),
        _bool_or_none(row.get("is_home")),
        _int_or_none(row.get("shots")),
        _int_or_none(row.get("shots_on_goal")),
        _int_or_none(row.get("goals")),
        _int_or_none(row.get("corners")),
        _int_or_none(row.get("saves")),
    )


def _player_stats_row(row: pd.Series, school_id: int) -> tuple:
    return (
        int(row["game_id"]),
        school_id,
        row.get("team"),
        str(row.get("jersey_number", "")),
        row.get("player_name"),
        row.get("position"),
        _bool_or_none(row.get("is_starter")),
        _int_or_none(row.get("minutes")),
        _int_or_none(row.get("shots")),
        _int_or_none(row.get("shots_on_goal")),
        _int_or_none(row.get("goals")),
        _int_or_none(row.get("assists")),
    )


def _events_row(row: pd.Series, school_id: int) -> tuple:
    return (
        int(row["game_id"]),
        school_id,
        row.get("event_type"),
        row.get("clock"),
        row.get("team"),
        row.get("player"),
        row.get("assist1"),
        row.get("assist2"),
        row.get("description"),
    )


TEAM_STATS_COLS = [
    "game_id", "school_id", "team", "is_home",
    "shots", "shots_on_goal", "goals", "corners", "saves",
]
PLAYER_STATS_COLS = [
    "game_id", "school_id", "team", "jersey_number", "player_name",
    "position", "is_starter", "minutes", "shots", "shots_on_goal",
    "goals", "assists",
]
EVENTS_COLS = [
    "game_id", "school_id", "event_type", "clock", "team",
    "player", "assist1", "assist2", "description",
]


def load_school(
    conn: psycopg2.extensions.connection,
    school_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    """Load all parquet data for one school directory. Returns row counts."""
    abbrev = school_dir.name.upper()

    # Prefer the merged "all" directory, fall back to per-year
    all_dir = school_dir / "all"
    if all_dir.exists():
        source = all_dir
    else:
        # Concatenate per-year parquets
        source = school_dir

    games_df = _read_merged_parquets(source, "games")
    team_stats_df = _read_merged_parquets(source, "team_stats")
    player_stats_df = _read_merged_parquets(source, "player_stats")
    events_df = _read_merged_parquets(source, "events")

    if games_df.empty:
        console.print(f"  [yellow]No games data found for {abbrev}")
        return {"games": 0, "team_game_stats": 0, "player_game_stats": 0, "game_events": 0}

    if dry_run:
        console.print(f"  [cyan]DRY RUN: would load {len(games_df)} games for {abbrev}")
        return {
            "games": len(games_df),
            "team_game_stats": len(team_stats_df),
            "player_game_stats": len(player_stats_df),
            "game_events": len(events_df),
        }

    cur = conn.cursor()

    # Ensure school exists and get its id
    school_id = _ensure_school(cur, abbrev)

    # Load in FK order: games first, then child tables
    n_games = _load_games(cur, games_df, school_id)

    n_team = _load_child_table(
        cur, "team_game_stats", team_stats_df, school_id,
        TEAM_STATS_COLS, _team_stats_row,
    )
    n_player = _load_child_table(
        cur, "player_game_stats", player_stats_df, school_id,
        PLAYER_STATS_COLS, _player_stats_row,
    )
    n_events = _load_child_table(
        cur, "game_events", events_df, school_id,
        EVENTS_COLS, _events_row,
    )

    conn.commit()
    return {
        "games": n_games,
        "team_game_stats": n_team,
        "player_game_stats": n_player,
        "game_events": n_events,
    }


def _read_merged_parquets(source: Path, kind: str) -> pd.DataFrame:
    """Read from merged parquet or concatenate per-year files."""
    merged = source / f"{kind}.parquet"
    if merged.exists():
        return pd.read_parquet(merged)

    # If source is a school dir (not "all"), gather per-year files
    frames: list[pd.DataFrame] = []
    for child in sorted(source.iterdir()):
        if child.is_dir() and child.name != "all":
            path = child / f"{kind}.parquet"
            if path.exists():
                frames.append(pd.read_parquet(path))
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


def main() -> None:
    """Entry point for ``uv run load-db``."""
    parser = argparse.ArgumentParser(
        description="Load parquet data into PostgreSQL",
    )
    parser.add_argument(
        "--school",
        type=str,
        default=None,
        help="School abbreviation filter (e.g. HU)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be loaded without writing to the database",
    )
    parser.add_argument(
        "--scrape-first",
        action="store_true",
        help="Run the scraper before loading if data/structured/ is empty",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="PostgreSQL connection URL (default: DATABASE_URL env or localhost:54321)",
    )
    args = parser.parse_args()

    database_url = args.database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

    # Check for parquet data; optionally scrape first
    school_dirs = _school_dirs(STRUCTURED_DIR, args.school)

    if not school_dirs and args.scrape_first:
        console.print("[bold blue]No parquet data found. Running scraper first...")
        from scripts.scrape import main as scrape_main

        scrape_argv = []
        if args.school:
            scrape_argv.extend(["--school", args.school])

        # Temporarily replace sys.argv for the scraper
        old_argv = sys.argv
        sys.argv = ["scrape"] + scrape_argv
        try:
            scrape_main()
        finally:
            sys.argv = old_argv

        # Re-scan after scraping
        school_dirs = _school_dirs(STRUCTURED_DIR, args.school)

    if not school_dirs:
        console.print(
            "[red]No data found in data/structured/. "
            "Run 'uv run scrape' first or use --scrape-first."
        )
        sys.exit(1)

    if args.dry_run:
        console.print("[bold yellow]DRY RUN — no database changes will be made\n")
        conn = None
    else:
        console.print("[bold blue]Connecting to database...")
        conn = _get_connection(database_url)
        console.print("[green]Connected.\n")

    summary = Table(title="Load Summary")
    summary.add_column("School", style="cyan")
    summary.add_column("Games", justify="right")
    summary.add_column("Team Stats", justify="right")
    summary.add_column("Player Stats", justify="right")
    summary.add_column("Events", justify="right")

    total = {"games": 0, "team_game_stats": 0, "player_game_stats": 0, "game_events": 0}

    for school_dir in school_dirs:
        abbrev = school_dir.name.upper()
        console.rule(f"[bold blue]{abbrev}")

        if args.dry_run:
            # For dry run, just count the parquet rows
            counts = load_school(None, school_dir, dry_run=True)
        else:
            counts = load_school(conn, school_dir, dry_run=False)

        for key in total:
            total[key] += counts[key]

        summary.add_row(
            abbrev,
            str(counts["games"]),
            str(counts["team_game_stats"]),
            str(counts["player_game_stats"]),
            str(counts["game_events"]),
        )

    summary.add_row(
        "[bold]TOTAL",
        f"[bold]{total['games']}",
        f"[bold]{total['team_game_stats']}",
        f"[bold]{total['player_game_stats']}",
        f"[bold]{total['game_events']}",
        style="bold",
    )

    console.print()
    console.print(summary)

    if conn:
        conn.close()
        console.print("\n[bold green]Load complete.")


if __name__ == "__main__":
    main()
