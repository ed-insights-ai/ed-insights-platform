"""Tests for src.parser — parse real cached HTML if available, else skip."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.parser import build_team_abbrev_map, parse_game, parse_game_header

CACHED_HTML = Path("data/raw_html/2025/game_01.html")


@pytest.mark.skipif(not CACHED_HTML.exists(), reason="No cached HTML for 2025 game 01")
def test_parse_cached_game():
    """Parse a real cached HTML page and assert basic structure."""
    html = CACHED_HTML.read_text(encoding="utf-8")
    result = parse_game(html, game_id=202501, source_url="http://test", season_year=2025)

    assert result["game"].season_year == 2025
    assert result["game"].game_id == 202501
    assert len(result["player_stats"]) > 0
    assert all(p.season_year == 2025 for p in result["player_stats"])
    assert isinstance(result["team_stats"], list)
    assert isinstance(result["events"], list)


def test_abbrev_map_no_hardcoded_harding():
    """Harding should resolve via generation logic, not a hardcoded default."""
    # With empty team_names, there should be no HU mapping
    result = build_team_abbrev_map("<html></html>", [])
    assert "HU" not in result

    # With Harding in team_names, HU should resolve
    result = build_team_abbrev_map("<html></html>", ["Harding"])
    assert "HU" in result or any("Harding" in v for v in result.values())


@pytest.mark.parametrize(
    ("title", "expected_date"),
    [
        ("Harding vs Dallas Baptist (Sep. 1, 2016)", "2016-09-01"),
        ("Harding vs Delta State (9/8/2017)", "2017-09-08"),
        ("Okla. Christian vs Harding (Sep 02, 2017)", "2017-09-02"),
        ("Harding vs Ouachita Baptist (09/13/16)", "2016-09-13"),
    ],
)
def test_parse_game_header_date_forms(title, expected_date):
    metadata = parse_game_header(f"<html><title>{title}</title></html>")

    assert metadata["date"] == expected_date


def test_header_state_paren_regression():
    metadata = parse_game_header(
        "<html><title>Harding vs Wayne St. (NE) (09/07/19)</title></html>"
    )

    assert metadata["away_team"] == "Wayne St. (NE)"
    assert metadata["date"] == "2019-09-07"


def test_parse_game_header_textual_date_venue_fallback():
    metadata = parse_game_header(
        "<html><title>Harding vs Northeastern State (Sep 08, 2017)</title>"
        "<body>(Sep 08, 2017 at Tahlequah, Okla.)</body></html>"
    )

    assert metadata["venue"] == "Tahlequah, Okla."


def test_statcrew_venue_places_harding_away_and_keeps_scores_aligned():
    html = Path("data/raw_html/hu/2025/game_09.html").read_text(encoding="utf-8")
    result = parse_game(
        html,
        game_id=1202509,
        source_url="http://test",
        season_year=2025,
        school_name="Harding",
    )
    game = result["game"]

    assert game.home_team == "Northeastern St."
    assert game.away_team == "Harding"
    assert game.home_score == 1
    assert game.away_score == 0
    assert game.neutral_site is False
    assert result["home_away_resolution"] == "venue-city-unmatched"


def test_statcrew_venue_overrides_order_when_harding_is_home():
    html = Path("data/raw_html/hu/2024/game_18.html").read_text(encoding="utf-8")
    result = parse_game(
        html,
        game_id=1202418,
        source_url="http://test",
        season_year=2024,
        school_name="Harding",
    )
    game = result["game"]

    assert game.home_team == "Harding"
    assert game.away_team == "Northeastern St."
    assert game.home_score == 3
    assert game.away_score == 5
    assert result["home_away_resolution"] == "resolved-by-venue"
