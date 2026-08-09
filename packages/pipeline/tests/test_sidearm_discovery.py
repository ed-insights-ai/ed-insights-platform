"""Tests for SideArm schedule discovery."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from src.sidearm_discovery import discover_sidearm_season

BASE_URL = "https://example.com/sports/mens-soccer"
OBUW_BASE_URL = "https://obutigers.com/sports/womens-soccer"


def _mock_response(html: str, *, url: str, history=()) -> MagicMock:
    response = MagicMock()
    response.text = html
    response.url = url
    response.history = list(history)
    return response


def _discover(
    year: int,
    html: str,
    *,
    base_url: str = BASE_URL,
    url: str | None = None,
    history=(),
):
    with patch("src.sidearm_discovery._build_session") as mock_session_fn:
        session = MagicMock()
        session.get.return_value = _mock_response(
            html,
            url=url or f"{base_url}/schedule/{year}",
            history=history,
        )
        mock_session_fn.return_value = session
        return discover_sidearm_season(year, base_url)


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


def test_redirect_to_bare_schedule_with_no_boxscores_fails_loudly(caplog):
    html = "<title>2026 Men's Soccer Schedule - Example Athletics</title>"

    with caplog.at_level(logging.ERROR, logger="src.sidearm_discovery"):
        games = _discover(
            2020,
            html,
            url=f"{BASE_URL}/schedule",
            history=[MagicMock()],
        )

    assert games == []
    assert (
        "[2020] Season slug redirected: requested "
        "https://example.com/sports/mens-soccer/schedule/2020 but served season "
        "2026 at https://example.com/sports/mens-soccer/schedule — a different "
        "season. Not ingesting."
        in caplog.messages
    )


def test_redirect_with_boxscores_fails_loudly(caplog):
    html = """
        <title>2025 Men's Soccer Schedule - Example Athletics</title>
        <a href="/sports/mens-soccer/stats/2025/opponent-a/boxscore/1">Box score</a>
        <a href="/sports/mens-soccer/stats/2025/opponent-b/boxscore/2">Box score</a>
    """

    with caplog.at_level(logging.ERROR, logger="src.sidearm_discovery"):
        games = _discover(
            2020,
            html,
            url=f"{BASE_URL}/schedule",
            history=[MagicMock()],
        )

    assert games == []
    assert any("served season 2025" in message for message in caplog.messages)


def test_no_redirect_empty_page_stays_quiet(caplog):
    with caplog.at_level(logging.ERROR, logger="src.sidearm_discovery"):
        games = _discover(2020, "")

    assert games == []
    assert not caplog.records


def test_benign_trailing_slash_redirect_ok():
    html = """
        <a href="/sports/mens-soccer/stats/2025/opponent-a/boxscore/1">Box score</a>
        <a href="/sports/mens-soccer/stats/2025/opponent-b/boxscore/2">Box score</a>
    """

    games = _discover(
        2025,
        html,
        url=f"{BASE_URL}/schedule/2025/",
        history=[MagicMock()],
    )

    assert len(games) == 2


def test_current_season_canonicalised_to_bare_schedule_is_accepted(caplog):
    """The common case once a season opens: /schedule/2026 302s to the canonical
    bare /schedule, which IS season 2026. Rejecting on URL shape alone would
    refuse the very season we asked for and return zero games."""
    html = """
        <title>2026 Men's Soccer Schedule - Example Athletics</title>
        <a href="/sports/mens-soccer/stats/2026/opponent-a/boxscore/1">Box score</a>
        <a href="/sports/mens-soccer/stats/2026/opponent-b/boxscore/2">Box score</a>
    """

    with caplog.at_level(logging.ERROR, logger="src.sidearm_discovery"):
        games = _discover(
            2026,
            html,
            url=f"{BASE_URL}/schedule",
            history=[MagicMock()],
        )

    assert len(games) == 2
    assert all(game.year == 2026 for game in games)
    assert not caplog.records


def test_redirect_to_covid_slug_is_the_same_season():
    """A 2020 request served at /schedule/2020-21 is season 2020, not a
    different season — compare on the leading year, not the whole slug."""
    html = """
        <a href="/sports/mens-soccer/stats/2020/opponent-a/boxscore/1">Box score</a>
    """

    games = _discover(
        2020,
        html,
        url=f"{BASE_URL}/schedule/2020-21",
        history=[MagicMock()],
    )

    assert len(games) == 1


def test_redirect_with_undeterminable_season_still_fails_loudly(caplog):
    """No year in the final path and none in the title — we cannot prove which
    season was served, so refuse rather than ingest on an assumption."""
    html = "<title>Men's Soccer Schedule - Example Athletics</title>"

    with caplog.at_level(logging.ERROR, logger="src.sidearm_discovery"):
        games = _discover(
            2026,
            html,
            url=f"{BASE_URL}/schedule",
            history=[MagicMock()],
        )

    assert games == []
    assert any("served season unknown" in message for message in caplog.messages)


def test_reachable_2020_season_still_succeeds():
    html = """
        <a href="/sports/womens-soccer/stats/2020/opponent-a/boxscore/1">Box score</a>
        <a href="/sports/womens-soccer/stats/2020/opponent-b/boxscore/2">Box score</a>
    """

    games = _discover(2020, html, base_url=OBUW_BASE_URL)

    assert len(games) == 2
    assert all(game.year == 2020 for game in games)
