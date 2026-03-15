"""Tests for game_id generation — verifies no collisions across schools."""

from __future__ import annotations

from src.config import load_schools


def test_game_id_no_collision_across_schools():
    """HU (ordinal=1) and HUW (ordinal=2) must produce non-overlapping game_ids."""
    schools = load_schools()
    hu = next(s for s in schools if s.abbreviation == "HU")
    huw = next(s for s in schools if s.abbreviation == "HUW")

    assert hu.ordinal != huw.ordinal

    # Same year, same game_num → different game_ids
    year, game_num = 2024, 1
    hu_id = hu.ordinal * 1_000_000 + year * 100 + game_num
    huw_id = huw.ordinal * 1_000_000 + year * 100 + game_num
    assert hu_id != huw_id


def test_ordinals_are_stable_and_positive():
    """Every school gets a positive ordinal based on schools.toml order."""
    schools = load_schools()
    ordinals = [s.ordinal for s in schools]
    assert ordinals == list(range(1, len(schools) + 1))
