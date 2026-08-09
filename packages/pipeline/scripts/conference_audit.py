"""CLI entry point for the independent conference-game derivation audit."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Literal

import psycopg2
from rich.console import Console
from rich.table import Table

from src.conference import AuditResult, audit_rows

_DEFAULT_DATABASE_URL = "dbname=ed_insights user=lume"
_CONFERENCE_QUERY = """\
SELECT
    g.game_id,
    s.gender,
    g.season_year,
    g.home_team,
    g.away_team,
    g.is_conference_game
FROM games g
JOIN schools s ON s.id = g.school_id
"""

Verdict = Literal["ok", "warn", "alarm"]
_SEVERITY: dict[Verdict, int] = {"ok": 0, "warn": 1, "alarm": 2}


def _raise_verdict(current: Verdict, candidate: Verdict) -> Verdict:
    if _SEVERITY[candidate] > _SEVERITY[current]:
        return candidate
    return current


def _verdict_for(result: AuditResult) -> Verdict:
    verdict: Verdict = "ok"
    if result.null_count:
        verdict = _raise_verdict(verdict, "warn")
    if result.disagreements:
        verdict = _raise_verdict(verdict, "alarm")
    if result.standing_violations:
        verdict = _raise_verdict(verdict, "alarm")
    if result.unresolved:
        verdict = _raise_verdict(verdict, "alarm")
    return verdict


def _headline(result: AuditResult) -> str:
    return (
        f"{len(result.disagreements)} of {result.total} rows disagree; "
        f"{result.null_count} NULL (not yet derived) of {result.total}; "
        f"{len(result.unresolved)} unresolved of {result.total}; "
        f"{len(result.standing_violations)} standing violations of {result.total}"
    )


def _cause(result: AuditResult, verdict: Verdict) -> str:
    if verdict == "alarm":
        return (
            "Stored conference flags disagree with the independent gender-aware, "
            "season-aware derivation, violate a standing exclusion, or include an "
            "unresolved team identity."
        )
    if verdict == "warn":
        return (
            "is_conference_game is not fully populated, so agreement cannot yet be "
            "verified for every row."
        )
    return ""


def _print_summary(result: AuditResult, verdict: Verdict) -> None:
    table = Table(title="Conference Derivation Audit")
    table.add_column("Measurement")
    table.add_column("Count", justify="right")
    table.add_column("Denominator", justify="right")
    table.add_row("Stored disagreements", str(len(result.disagreements)), str(result.total))
    table.add_row("NULL stored flags", str(result.null_count), str(result.total))
    table.add_row("Unresolved identities", str(len(result.unresolved)), str(result.total))
    table.add_row(
        "Standing violations",
        str(len(result.standing_violations)),
        str(result.total),
    )
    Console().print(table)
    Console().print(f"[bold]Verdict:[/bold] {verdict.upper()}")


def _result_payload(result: AuditResult) -> dict[str, str]:
    verdict = _verdict_for(result)
    return {
        "check": "conference-derivation",
        "verdict": verdict,
        "headline": _headline(result),
        "cause": _cause(result, verdict),
    }


def _failure_payload(error: Exception) -> dict[str, str]:
    return {
        "check": "conference-derivation",
        "verdict": "alarm",
        "headline": (
            "CHECK DID NOT RUN — the conference derivation query or audit failed, "
            "so no rows were measured."
        ),
        "cause": f"{type(error).__name__}: {error}",
    }


def _fetch_rows(database_url: str) -> list[dict[str, object]]:
    with psycopg2.connect(database_url) as connection:
        connection.set_session(readonly=True)
        with connection.cursor() as cursor:
            cursor.execute(_CONFERENCE_QUERY)
            columns = [description.name for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def main() -> None:
    """Run the conference derivation audit."""
    parser = argparse.ArgumentParser(
        description="Audit stored conference-game flags against an independent derivation"
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="PostgreSQL connection URL or DSN",
    )
    args = parser.parse_args()
    database_url = args.database_url or os.environ.get(
        "DATABASE_URL",
        _DEFAULT_DATABASE_URL,
    )

    try:
        result = audit_rows(_fetch_rows(database_url))
    except (psycopg2.Error, KeyError, TypeError, ValueError) as error:
        print(json.dumps(_failure_payload(error), separators=(",", ":")))
        sys.exit(1)

    verdict = _verdict_for(result)
    _print_summary(result, verdict)
    print(json.dumps(_result_payload(result), separators=(",", ":")))


if __name__ == "__main__":
    main()
