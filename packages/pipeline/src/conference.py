"""Independent GAC conference-game derivation.

The 2019 affiliate boundary comes from docs/UI_DESIGN.md:18 and
docs/specs/touchline-rib.md:647-659, not from the loader's backfill inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src import canon

AFFILIATES_SINCE_2019 = {
    "fort-hays-state",
    "newman",
    "northeastern-state",
    "rogers-state",
}
_WOMEN_STANDING_EXCLUSIONS = {
    "newman",
    "northeastern-state",
    "rogers-state",
}


@dataclass
class AuditResult:
    """Aggregate conference derivation findings."""

    total: int
    null_count: int
    unresolved: list[int | str]
    disagreements: list[dict[str, object]]
    standing_violations: list[dict[str, object]]


def is_gac_member(slug: str, gender: str, season_year: int) -> bool:
    """Return whether a programme was a GAC member for the given season."""
    programme = canon.PROGRAMMES.get(f"{slug}:{gender}")
    if programme is None or programme.get("school_row") is not True:
        return False
    return not (
        gender == "men"
        and slug in AFFILIATES_SINCE_2019
        and season_year < 2019
    )


def _resolve_slug(team: str) -> tuple[str | None, bool]:
    try:
        resolution = canon.resolve(team)
    except ValueError:
        return None, False

    classification = resolution["classification"]
    slug = resolution["institution_slug"]
    if classification == "artifact":
        return None, False
    if classification == "non_member":
        return None, resolution["adjudicated"]
    return slug, slug is not None


def derive(
    home_team: str,
    away_team: str,
    gender: str,
    season_year: int,
) -> tuple[bool | None, bool]:
    """Derive conference status and whether both team identities were resolved."""
    home_slug, home_resolved = _resolve_slug(home_team)
    away_slug, away_resolved = _resolve_slug(away_team)
    if not home_resolved or not away_resolved:
        return None, False

    derived = (
        home_slug is not None
        and away_slug is not None
        and is_gac_member(home_slug, gender, season_year)
        and is_gac_member(away_slug, gender, season_year)
    )
    return derived, True


def _required_string(row: dict[str, object], key: str) -> str:
    value = row[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _required_year(row: dict[str, object]) -> int:
    value = row["season_year"]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("season_year must be an integer")
    return value


def _stored_flag(row: dict[str, object]) -> bool | None:
    value = row["is_conference_game"]
    if value is not None and not isinstance(value, bool):
        raise TypeError("is_conference_game must be a boolean or None")
    return value


def audit_rows(rows: Iterable[dict[str, object]]) -> AuditResult:
    """Audit stored conference flags against the independent derivation."""
    total = 0
    null_count = 0
    unresolved: list[int | str] = []
    disagreements: list[dict[str, object]] = []
    standing_violations: list[dict[str, object]] = []

    for row in rows:
        total += 1
        game_id = row["game_id"]
        if not isinstance(game_id, (int, str)) or isinstance(game_id, bool):
            raise TypeError("game_id must be an integer or string")

        gender = _required_string(row, "gender")
        season_year = _required_year(row)
        home_team = _required_string(row, "home_team")
        away_team = _required_string(row, "away_team")
        stored = _stored_flag(row)
        if stored is None:
            null_count += 1

        home_slug, home_resolved = _resolve_slug(home_team)
        away_slug, away_resolved = _resolve_slug(away_team)
        derived, identities_resolved = derive(
            home_team,
            away_team,
            gender,
            season_year,
        )
        if not identities_resolved:
            unresolved.append(game_id)
            continue

        if stored is not None and stored != derived:
            disagreements.append(
                {"game_id": game_id, "stored": stored, "derived": derived}
            )

        if stored is not True or not home_resolved or not away_resolved:
            continue

        slugs = {home_slug, away_slug}
        if gender == "women" and slugs & _WOMEN_STANDING_EXCLUSIONS:
            standing_violations.append(
                {"game_id": game_id, "rule": "women-vs-mens-affiliate"}
            )
        if gender == "men" and "oklahoma-baptist" in slugs:
            standing_violations.append(
                {"game_id": game_id, "rule": "men-vs-oklahoma-baptist"}
            )
        if (
            gender == "men"
            and season_year < 2019
            and slugs & AFFILIATES_SINCE_2019
        ):
            standing_violations.append(
                {"game_id": game_id, "rule": "pre-2019-men-vs-affiliate"}
            )

    return AuditResult(
        total=total,
        null_count=null_count,
        unresolved=unresolved,
        disagreements=disagreements,
        standing_violations=standing_violations,
    )
