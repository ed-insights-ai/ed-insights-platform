"""Tests for venue-based home/away resolution."""

import pytest

from src.home_cities import HOME_CITY, resolve_home_away, venue_city


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Searcy, Ark.", "Searcy"),
        ("Searcy, UNITED STATE", "Searcy"),
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
