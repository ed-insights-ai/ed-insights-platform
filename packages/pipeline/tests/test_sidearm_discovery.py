"""Tests for SideArm schedule discovery."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from src.sidearm_discovery import discover_sidearm_season

BASE_URL = "https://example.com/sports/mens-soccer"


def _mock_response(html: str) -> MagicMock:
    response = MagicMock()
    response.text = html
    return response


def _discover(year: int, html: str):
    with patch("src.sidearm_discovery._build_session") as mock_session_fn:
        session = MagicMock()
        session.get.return_value = _mock_response(html)
        mock_session_fn.return_value = session
        return discover_sidearm_season(year, BASE_URL)


def test_rejects_wrong_season_paths():
    html = """
        <a href="/sports/mens-soccer/stats/2025/opponent-a/boxscore/1">Box score</a>
        <a href="/sports/mens-soccer/stats/2025/opponent-b/boxscore/2">Box score</a>
    """

    assert _discover(2020, html) == []


def test_discovers_correct_season_paths():
    html = """
        <a href="/sports/mens-soccer/stats/2025/opponent-a/boxscore/1">Box score</a>
        <a href="/sports/mens-soccer/stats/2025/opponent-b/boxscore/2">Box score</a>
    """

    games = _discover(2025, html)

    assert len(games) == 2
    assert all(game.year == 2025 for game in games)


def test_filters_mixed_season_paths():
    html = """
        <a href="/sports/mens-soccer/stats/2024/opponent-a/boxscore/1">Box score</a>
        <a href="/sports/mens-soccer/stats/2025/opponent-b/boxscore/2">Box score</a>
    """

    games = _discover(2025, html)

    assert len(games) == 1
    assert "/stats/2025/" in games[0].url


def test_all_rejected_logs_observed_year(caplog):
    html = """
        <a href="/sports/mens-soccer/stats/2025/opponent-a/boxscore/1">Box score</a>
        <a href="/sports/mens-soccer/stats/2025/opponent-b/boxscore/2">Box score</a>
    """

    with caplog.at_level(logging.ERROR, logger="src.sidearm_discovery"):
        games = _discover(2026, html)

    assert games == []
    assert (
        "[2026] Rejected 2 of 2 boxscore URLs — schedule page served season 2025. "
        "Not ingesting."
        in caplog.messages
    )
