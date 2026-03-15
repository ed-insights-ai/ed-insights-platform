"""Tests for src.discovery — mocked HTTP, content-size threshold."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.discovery import discover_season_games


def _mock_response(size: int) -> MagicMock:
    resp = MagicMock()
    resp.content = b"x" * size
    return resp


def test_stops_on_small_content():
    """A 999-byte response should stop discovery immediately."""
    with patch("src.discovery._build_session") as mock_session_fn:
        session = MagicMock()
        session.get.return_value = _mock_response(999)
        mock_session_fn.return_value = session

        games = discover_season_games(2025, max_probe=5)
        assert games == []


def test_continues_on_large_content():
    """A 1001-byte response should be treated as a valid game."""
    with patch("src.discovery._build_session") as mock_session_fn:
        session = MagicMock()
        # First call: valid, second call: empty → stop
        session.get.side_effect = [_mock_response(1001), _mock_response(999)]
        mock_session_fn.return_value = session

        games = discover_season_games(2025, max_probe=5)
        assert len(games) == 1
        assert games[0].year == 2025
        assert games[0].game_num == 1
