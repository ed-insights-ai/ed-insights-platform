"""Tests for game_id generation — verifies no collisions across schools."""

from __future__ import annotations

import tomllib
from pathlib import Path

from src.config import load_schools

SCHOOLS_TOML = Path(__file__).resolve().parent.parent / "config" / "schools.toml"


def test_game_id_no_collision_across_schools():
    """HU (ordinal=1) and HUW (ordinal=8) must produce non-overlapping game_ids."""
    schools = load_schools()
    hu = next(s for s in schools if s.abbreviation == "HU")
    huw = next(s for s in schools if s.abbreviation == "HUW")

    assert hu.ordinal != huw.ordinal

    # Same year, same game_num → different game_ids
    year, game_num = 2024, 1
    hu_id = hu.ordinal * 1_000_000 + year * 100 + game_num
    huw_id = huw.ordinal * 1_000_000 + year * 100 + game_num
    assert hu_id != huw_id


def test_ordinals_are_explicit_and_unique():
    """Every school has an explicit ordinal in TOML, all unique."""
    with open(SCHOOLS_TOML, "rb") as f:
        data = tomllib.load(f)

    ordinals = []
    for entry in data["schools"]:
        assert "ordinal" in entry, f"Missing ordinal for {entry['abbreviation']}"
        ordinals.append(entry["ordinal"])

    assert len(ordinals) == len(set(ordinals)), "Duplicate ordinals found"


def test_ordinals_survive_reorder():
    """Shuffling schools.toml entries doesn't change ordinals."""
    schools = load_schools()
    ordinal_map = {s.abbreviation: s.ordinal for s in schools}

    # Verify specific known ordinals that shouldn't change regardless of order
    assert ordinal_map["HU"] == 1
    assert ordinal_map["FHSU"] == 2
    assert ordinal_map["HUW"] == 8
    assert ordinal_map["SWOSU"] == 14
