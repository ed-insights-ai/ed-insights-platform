"""Tests for src.parser — parse real cached HTML if available, else skip."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.parser import build_team_abbrev_map, parse_game

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
