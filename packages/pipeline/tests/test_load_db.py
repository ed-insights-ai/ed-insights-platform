"""Tests for database-loading value normalization."""

from __future__ import annotations

import pytest
import pandas as pd

from scripts.load_db import _load_games, _str_or_none


@pytest.mark.parametrize("value", [float("nan"), "NaN", None])
def test_str_or_none_returns_none_for_missing_values(value):
    assert _str_or_none(value) is None


def test_str_or_none_strips_real_text():
    assert _str_or_none("  Dallas, TX ") == "Dallas, TX"


class RecordingCursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, params):
        self.calls.append((query, params))


@pytest.mark.parametrize(
    ("neutral_site", "expected"),
    [(True, True), (False, False), (None, False)],
)
def test_load_games_persists_neutral_site(neutral_site, expected):
    row = {
        "game_id": 1,
        "season_year": 2025,
        "source_url": "https://example.test/game",
        "date": "2025-10-01",
        "venue": "Hot Springs, Ark.",
        "attendance": 100,
        "home_team": "Harding",
        "away_team": "Ouachita Baptist",
        "home_score": 1,
        "away_score": 0,
    }
    if neutral_site is not None:
        row["neutral_site"] = neutral_site
    cursor = RecordingCursor()

    assert _load_games(cursor, pd.DataFrame([row]), school_id=7) == 1

    query, params = cursor.calls[0]
    assert "neutral_site" in query
    assert "neutral_site = EXCLUDED.neutral_site" in query
    assert params[11] is expected
