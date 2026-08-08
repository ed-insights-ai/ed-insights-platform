"""Build and validate the committed team-string identity artifact."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg2

from src.canon import ADJUDICATIONS, PROGRAMMES, REGISTRY, normalize, resolve

DEFAULT_DATABASE_URL = "postgresql://lume@localhost:5432/ed_insights"
CANON_PATH = Path(__file__).resolve().parents[1] / "data" / "reference" / "canon.json"
SOURCE_COLUMNS = (
    "games.home_team",
    "games.away_team",
    "team_game_stats.team",
    "player_game_stats.team",
    "game_events.team",
)

TEAM_STRINGS_SQL = """
WITH team_strings(value) AS (
    SELECT home_team FROM games
    UNION
    SELECT away_team FROM games
    UNION
    SELECT team FROM team_game_stats
    UNION
    SELECT team FROM player_game_stats
    UNION
    SELECT team FROM game_events
)
SELECT value
FROM team_strings
WHERE value IS NOT NULL AND btrim(value) <> ''
ORDER BY value
"""

INVALID_TEAM_STRINGS_SQL = """
WITH team_strings(value) AS (
    SELECT home_team FROM games
    UNION ALL
    SELECT away_team FROM games
    UNION ALL
    SELECT team FROM team_game_stats
    UNION ALL
    SELECT team FROM player_game_stats
    UNION ALL
    SELECT team FROM game_events
)
SELECT
    count(*) FILTER (WHERE value IS NULL),
    count(*) FILTER (WHERE value IS NOT NULL AND btrim(value) = '')
FROM team_strings
"""

VALID_CLASSIFICATIONS = {"institution_slug", "non_member", "artifact"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or check data/reference/canon.json against PostgreSQL."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the committed artifact without rewriting it.",
    )
    return parser.parse_args()


def fetch_team_strings(database_url: str) -> list[str]:
    """Read the complete, non-empty team-string universe from PostgreSQL."""
    with psycopg2.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(INVALID_TEAM_STRINGS_SQL)
            null_count, empty_count = cursor.fetchone()
            if null_count or empty_count:
                raise ValueError(
                    "source universe contains invalid keys: "
                    f"{null_count} NULL and {empty_count} empty"
                )

            cursor.execute(TEAM_STRINGS_SQL)
            team_strings = [row[0] for row in cursor.fetchall()]

    if not team_strings:
        raise ValueError("source universe is empty")
    return team_strings


def build_document(team_strings: list[str]) -> dict[str, Any]:
    """Construct the serializable canon document for a measured universe."""
    opponents = {team: resolve(team) for team in team_strings}
    return {
        "version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_columns": list(SOURCE_COLUMNS),
        "distinct_string_count": len(team_strings),
        "institutions": REGISTRY,
        "programmes": PROGRAMMES,
        "opponents": opponents,
    }


def _resolution_identity(resolution: dict[str, Any]) -> tuple[str, str | None]:
    return (
        resolution.get("classification"),
        resolution.get("institution_slug"),
    )


def validate_document(
    document: dict[str, Any],
    team_strings: list[str],
) -> list[str]:
    """Return every contract violation found in a canon document."""
    errors: list[str] = []
    opponents = document.get("opponents")
    if not isinstance(opponents, dict):
        return ["opponents must be a JSON object"]

    measured_keys = set(team_strings)
    artifact_keys = set(opponents)
    missing = sorted(measured_keys - artifact_keys)
    extra = sorted(artifact_keys - measured_keys)
    if missing:
        errors.append(f"missing {len(missing)} measured keys: {missing}")
    if extra:
        errors.append(f"contains {len(extra)} stale keys: {extra}")
    if document.get("distinct_string_count") != len(team_strings):
        errors.append(
            "distinct_string_count does not equal the measured universe "
            f"({document.get('distinct_string_count')!r} != {len(team_strings)})"
        )
    if document.get("source_columns") != list(SOURCE_COLUMNS):
        errors.append("source_columns does not declare the five measured columns")

    normalized_identities: dict[str, dict[tuple[str, str | None], list[str]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    for raw_key, resolution in opponents.items():
        if not isinstance(raw_key, str) or not raw_key.strip():
            errors.append(f"invalid opponent key: {raw_key!r}")
            continue
        if not isinstance(resolution, dict):
            errors.append(f"{raw_key!r} resolution must be an object")
            continue

        classification = resolution.get("classification")
        slug = resolution.get("institution_slug")
        if classification not in VALID_CLASSIFICATIONS:
            errors.append(f"{raw_key!r} has invalid classification {classification!r}")
        elif classification == "institution_slug":
            if slug not in REGISTRY:
                errors.append(f"{raw_key!r} has unknown institution slug {slug!r}")
        elif slug is not None:
            errors.append(f"{raw_key!r} has {classification!r} classification and a slug")

        if resolution.get("adjudicated"):
            note = resolution.get("note")
            if not isinstance(note, str) or not note.strip():
                errors.append(f"{raw_key!r} is adjudicated without an evidence note")
            if classification == "artifact" and "game_id" not in (note or ""):
                errors.append(f"{raw_key!r} artifact note does not name a game_id")
        elif resolution.get("note") is not None:
            errors.append(f"{raw_key!r} has a note but is not adjudicated")

        normalized_identities[normalize(raw_key)][
            _resolution_identity(resolution)
        ].append(raw_key)

    for normalized_key, identities in normalized_identities.items():
        if len(identities) > 1:
            collisions = {
                f"{classification}:{slug}": sorted(raw_keys)
                for (classification, slug), raw_keys in identities.items()
            }
            errors.append(
                f"normalized key {normalized_key!r} crosses identities: {collisions}"
            )

    for raw_key, expected in ADJUDICATIONS.items():
        actual = opponents.get(raw_key)
        if actual is None:
            errors.append(f"adjudicated key {raw_key!r} is absent")
            continue
        expected_identity = (
            expected["classification"],
            expected["institution_slug"],
        )
        if _resolution_identity(actual) != expected_identity:
            errors.append(
                f"adjudicated key {raw_key!r} has identity "
                f"{_resolution_identity(actual)!r}, expected {expected_identity!r}"
            )
        if actual.get("adjudicated") is not True:
            errors.append(f"adjudicated key {raw_key!r} is not flagged adjudicated")

    if "Southwestern Christi." in opponents:
        errors.append("invented nonexistent key 'Southwestern Christi.'")
    if normalize("Southwestern") == normalize("Southwestern (KS)"):
        errors.append("normalizer merges Southwestern with Southwestern (KS)")

    institutions = document.get("institutions")
    if institutions != REGISTRY:
        errors.append("institutions does not match the authoritative registry")
    programmes = document.get("programmes")
    if programmes != PROGRAMMES:
        errors.append("programmes does not match the declared programme universe")
    declared_slugs = {
        programme["institution_slug"] for programme in PROGRAMMES.values()
    }
    resolved_slugs = {
        resolution.get("institution_slug")
        for resolution in opponents.values()
        if isinstance(resolution, dict)
        and resolution.get("classification") == "institution_slug"
    }
    undeclared_slugs = sorted(resolved_slugs - declared_slugs)
    if undeclared_slugs:
        errors.append(f"resolved slugs lack programme declarations: {undeclared_slugs}")

    return errors


def _summary(document: dict[str, Any], measured_count: int) -> str:
    opponents = document["opponents"]
    classifications = [
        resolution["classification"] for resolution in opponents.values()
    ]
    adjudicated_count = sum(
        resolution["adjudicated"] for resolution in opponents.values()
    )
    return (
        f"covered {len(opponents)}/{measured_count}, "
        f"adjudicated {adjudicated_count}, "
        f"institutions {classifications.count('institution_slug')}, "
        f"non-members {classifications.count('non_member')}, "
        f"artifacts {classifications.count('artifact')}"
    )


def _load_document() -> dict[str, Any]:
    with CANON_PATH.open(encoding="utf-8") as canon_file:
        document = json.load(canon_file)
    if not isinstance(document, dict):
        raise ValueError("canon.json root must be a JSON object")
    return document


def _write_document(document: dict[str, Any]) -> None:
    CANON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CANON_PATH.open("w", encoding="utf-8", newline="\n") as canon_file:
        json.dump(document, canon_file, indent=2, sort_keys=True, ensure_ascii=True)
        canon_file.write("\n")


def main() -> int:
    """Run the build or check command."""
    args = _parse_args()
    database_url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

    try:
        team_strings = fetch_team_strings(database_url)
        if args.check:
            document = _load_document()
        else:
            document = build_document(team_strings)
            _write_document(document)

        errors = validate_document(document, team_strings)
    except (json.JSONDecodeError, OSError, psycopg2.Error, ValueError) as error:
        print(f"build-canon failed: {error}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"build-canon failed: {error}", file=sys.stderr)
        return 1

    print(_summary(document, len(team_strings)))
    if not args.check:
        print(f"wrote {CANON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
