"""Contract tests for the canonical team-string identity map."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import psycopg2
import pytest

from scripts.build_canon import CANON_PATH, SOURCE_COLUMNS, fetch_team_strings
from src.canon import ADJUDICATIONS, ALIASES, PROGRAMMES, REGISTRY, normalize, resolve

DATABASE_URL = os.environ.get("DATABASE_URL")
VALID_CLASSIFICATIONS = {"institution_slug", "non_member", "artifact"}


@pytest.fixture(scope="module")
def canon_document() -> dict:
    return json.loads(Path(CANON_PATH).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("#16 Fort Hays St.", "fort hays state"),
        ("#16 Northeastern State", "northeastern state"),
        ("#16 Southern Nazarene", "southern nazarene"),
        ("#19 Southern Nazarene", "southern nazarene"),
        ("Newman  NU", "newman"),
        ("Okla. Baptist  OKLA.", "oklahoma baptist"),
        ("Okla. Christian  OK", "oklahoma christian"),
    ],
)
def test_normalize_observed_source_variants(raw_value, expected):
    assert normalize(raw_value) == expected


def test_normalize_preserves_distinguishing_parenthetical():
    assert normalize("Southwestern") != normalize("Southwestern (KS)")
    assert normalize("Southwestern (KS)") == "southwestern (ks)"


@pytest.mark.parametrize("raw_value", ["", " ", "\t"])
def test_normalize_rejects_empty_keys(raw_value):
    with pytest.raises(ValueError, match="must not be empty"):
        normalize(raw_value)


@pytest.mark.parametrize(
    ("raw_value", "expected_slug"),
    [
        ("Northwestern OSU", "northwestern-oklahoma-state"),
        ("Southwestern OSU", "southwestern-oklahoma-state"),
        ("Southwestern", "southwestern-oklahoma-state"),
        ("SOUTHWES", "southwestern-oklahoma-state"),
        ("NSU", "northeastern-state"),
        ("NC", "newman"),
    ],
)
def test_must_resolve_adjudications(raw_value, expected_slug):
    resolution = resolve(raw_value)

    assert resolution["classification"] == "institution_slug"
    assert resolution["institution_slug"] == expected_slug
    assert resolution["adjudicated"] is True
    assert resolution["note"]


@pytest.mark.parametrize(
    "raw_value",
    [
        "Southwest Baptist",
        "Dallas Baptist",
        "DBU",
        "Williams Baptist",
        "WBC",
        "Central Baptist",
        "Central Baptist (AR)",
        "CBC",
        "Southwestern Christ.",
        "Southwestern Christi",
        "SW Christian",
        "Southwestern (KS)",
        "Western",
        "ESU",
        "OU",
    ],
)
def test_must_not_resolve_adjudications(raw_value):
    resolution = resolve(raw_value)

    assert resolution["classification"] == "non_member"
    assert resolution["institution_slug"] is None
    assert resolution["adjudicated"] is True
    assert resolution["note"]


@pytest.mark.parametrize(
    ("raw_value", "expected_slug"),
    [
        ("HU", "harding"),
        ("OKBU", "oklahoma-baptist"),
        ("SNU", "southern-nazarene"),
    ],
)
def test_abbreviation_lookalikes_resolve_without_gender(raw_value, expected_slug):
    resolution = resolve(raw_value)

    assert resolution["institution_slug"] == expected_slug
    assert "gender" not in resolution


def test_aliases_are_disjoint_after_normalization():
    owners: dict[str, str] = {}
    for slug, aliases in ALIASES.items():
        for alias in aliases:
            assert normalize(alias) == alias
            assert alias not in owners or owners[alias] == slug
            owners[alias] = slug


def test_artifact_matches_documented_schema(canon_document):
    assert canon_document["version"] == 1
    datetime.fromisoformat(canon_document["generated_at"])
    assert canon_document["source_columns"] == list(SOURCE_COLUMNS)
    assert canon_document["distinct_string_count"] == len(
        canon_document["opponents"]
    )
    assert canon_document["institutions"] == REGISTRY
    assert canon_document["programmes"] == PROGRAMMES

    for raw_key, resolution in canon_document["opponents"].items():
        assert raw_key.strip()
        assert resolution["classification"] in VALID_CLASSIFICATIONS
        assert set(resolution) == {
            "adjudicated",
            "classification",
            "institution_slug",
            "note",
        }
        assert "gender" not in resolution
        if resolution["classification"] == "institution_slug":
            assert resolution["institution_slug"] in REGISTRY
        else:
            assert resolution["institution_slug"] is None


def test_adjudications_and_artifacts_have_evidence(canon_document):
    opponents = canon_document["opponents"]
    assert "Southwestern Christi." not in opponents

    for raw_key, adjudication in ADJUDICATIONS.items():
        resolution = opponents[raw_key]
        assert resolution["adjudicated"] is True
        assert resolution["note"]
        assert (
            resolution["classification"],
            resolution["institution_slug"],
        ) == (
            adjudication["classification"],
            adjudication["institution_slug"],
        )

    artifacts = {
        raw_key
        for raw_key, resolution in opponents.items()
        if resolution["classification"] == "artifact"
    }
    assert {
        "NU Cli",
        "NWOSU18",
        "OKLA. BA",
        "UAPBWS17",
    } <= artifacts
    for raw_key in artifacts:
        assert "game_id" in opponents[raw_key]["note"]


def test_normalized_keys_do_not_cross_identities(canon_document):
    normalized_identities: dict[str, set[tuple[str, str | None]]] = defaultdict(set)
    for raw_key, resolution in canon_document["opponents"].items():
        normalized_identities[normalize(raw_key)].add(
            (
                resolution["classification"],
                resolution["institution_slug"],
            )
        )

    collisions = {
        normalized_key: identities
        for normalized_key, identities in normalized_identities.items()
        if len(identities) > 1
    }
    assert not collisions
    assert normalize("Southwestern") != normalize("Southwestern (KS)")


def test_programme_universe_declares_missing_and_disabled_rows(canon_document):
    programmes = canon_document["programmes"]
    expected_missing = {
        "fort-hays-state:women",
        "newman:women",
        "northeastern-state:women",
        "oklahoma-baptist:men",
        "rogers-state:women",
    }
    assert all(
        programmes[key]["school_row"] is False
        and programmes[key]["enabled"] is None
        for key in expected_missing
    )
    assert programmes["northeastern-state:men"]["school_row"] is True
    assert programmes["northeastern-state:men"]["enabled"] is False

    declared_slugs = {
        programme["institution_slug"] for programme in programmes.values()
    }
    resolved_slugs = {
        resolution["institution_slug"]
        for resolution in canon_document["opponents"].values()
        if resolution["classification"] == "institution_slug"
    }
    assert resolved_slugs <= declared_slugs


@pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL is not set")
def test_live_database_universe_is_fully_covered(canon_document):
    team_strings = fetch_team_strings(DATABASE_URL)
    artifact_keys = set(canon_document["opponents"])

    assert artifact_keys == set(team_strings), (
        f"covered {len(artifact_keys & set(team_strings))}/{len(team_strings)}"
    )
    assert canon_document["distinct_string_count"] == len(team_strings)


@pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL is not set")
def test_source_url_gender_agrees_with_school_row():
    with psycopg2.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH classified AS (
                    SELECT
                        schools.gender,
                        CASE
                            WHEN games.source_url
                                ~ '/(womens-soccer|wsoc)(/|$)'
                                THEN 'women'
                            WHEN games.source_url
                                ~ '/(mens-soccer|msoc)(/|$)'
                                THEN 'men'
                        END AS source_gender
                    FROM games
                    JOIN schools ON schools.id = games.school_id
                )
                SELECT
                    count(*),
                    count(*) FILTER (WHERE source_gender IS NULL),
                    count(*) FILTER (
                        WHERE source_gender IS DISTINCT FROM gender
                    )
                FROM classified
                """
            )
            total_count, unclassified_count, mismatch_count = cursor.fetchone()

    assert total_count > 0
    assert unclassified_count == 0, f"{unclassified_count}/{total_count} unclassified"
    assert mismatch_count == 0, f"{mismatch_count}/{total_count} gender mismatches"
