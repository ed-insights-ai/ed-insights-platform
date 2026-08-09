"""Tests for venue-based home/away resolution."""

import pytest

from src.home_cities import (
    HOME_CITY,
    resolve_home_away,
    team_home_city,
    venue_city,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Searcy, Ark.", "Searcy"),
        ("Searcy, UNITED STATE", "Searcy"),
        ("Weatherford Okla.", "Weatherford"),
        ("Searcy. Ark.", "Searcy"),
        ("UNITED STATES", None),
        ("U", None),
        ("0", None),
        (None, None),
    ],
)
def test_venue_city_normalizes_first_segment(raw, expected):
    assert venue_city(raw) == expected


def test_home_city_map_covers_scraping_programs():
    assert HOME_CITY["HU"] == "Searcy"
    assert HOME_CITY["ECU"] == "Ada"
    assert HOME_CITY["SWOSU"] == "Weatherford"
    assert HOME_CITY["NSU"] == "Tahlequah"


def test_team_home_city_prefers_name_for_ambiguous_abbreviation():
    assert team_home_city("OBU", "Oklahoma Baptist") == "Shawnee"
    assert team_home_city("OUA", "Ouachita") == "Arkadelphia"


@pytest.mark.parametrize(
    ("venue", "opponent_city", "school_is_row0", "expected"),
    [
        ("Ada, Okla.", "Claremore", True, ("home", "resolved-by-venue")),
        ("Claremore, Okla.", "Claremore", True, ("away", "resolved-by-venue")),
        (None, "Claremore", True, ("away", "resolved-by-order-fallback")),
        ("0", "Claremore", False, ("home", "resolved-by-order-fallback")),
        ("Searcy, Ark.", "Claremore", True, ("neutral", "neutral")),
    ],
)
def test_resolve_home_away_reports_evidence(
    venue, opponent_city, school_is_row0, expected
):
    assert (
        resolve_home_away(
            "Ada",
            venue,
            opponent_city,
            school_is_row0,
            order_says_school_home=False,
        )
        == expected
    )


def test_unmatched_city_uses_order_without_claiming_neutral():
    assert resolve_home_away(
        "Searcy",
        "Tahlelquah, Okla., U",
        "Tahlequah",
        school_is_row0=True,
        order_says_school_home=False,
    ) == ("away", "venue-city-unmatched")


def test_near_miss_home_city_is_unmatched_not_neutral():
    assert resolve_home_away(
        "Arkadelphia",
        "Arkadelhpia High",
        "Alva",
        school_is_row0=False,
        order_says_school_home=False,
    ) == ("home", "venue-city-unmatched")


def test_valid_third_city_is_neutral_when_both_team_cities_are_known():
    assert resolve_home_away(
        "Arkadelphia",
        "Hot Springs, Ark.",
        "Searcy",
        school_is_row0=False,
        order_says_school_home=False,
    ) == ("neutral", "neutral")


def test_known_home_field_alias_resolves_to_canonical_city():
    assert resolve_home_away(
        "Bethany",
        "Maize, Kan.",
        "Wichita",
        school_is_row0=True,
        order_says_school_home=False,
    ) == ("away", "resolved-by-venue")


def test_unknown_opponent_city_is_explicit_order_fallback():
    assert resolve_home_away(
        "Searcy",
        "Portales, N.M.",
        None,
        school_is_row0=True,
        order_says_school_home=False,
    ) == ("away", "resolved-by-order-fallback")
