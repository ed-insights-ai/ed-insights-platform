"""Tests for src.storage — fake parsed game dicts → assert parquet files exist."""

from __future__ import annotations

import pandas as pd

from src.models import Game, GameEvent, PlayerGameStats, TeamGameStats
from src.storage import merge_all_seasons, save_season


def _fake_parsed_game(year: int = 2099) -> dict:
    game_id = int(f"{year}01")
    return {
        "game": Game(
            game_id=game_id,
            season_year=year,
            source_url="http://test",
            date="01/01/99",
            venue="Test Field",
            attendance=100,
            home_team="Team A",
            away_team="Team B",
            home_score=2,
            away_score=1,
        ),
        "player_stats": [
            PlayerGameStats(
                game_id=game_id,
                season_year=year,
                team="Team A",
                jersey_number=10,
                player_name="Test Player",
                position="F",
                is_starter=True,
                goals=1,
            ),
        ],
        "team_stats": [
            TeamGameStats(
                game_id=game_id,
                season_year=year,
                team="Team A",
                is_home=True,
                goals=2,
                shots=5,
            ),
            TeamGameStats(
                game_id=game_id,
                season_year=year,
                team="Team B",
                is_home=False,
                goals=1,
                shots=3,
            ),
        ],
        "events": [
            GameEvent(
                game_id=game_id,
                season_year=year,
                event_type="goal",
                clock="10:00",
                team="Team A",
                player="Test Player",
            ),
        ],
        "abbrev_map": {},
    }


def _fake_parsed_game_with_events(descriptions: list[str]) -> dict:
    parsed_game = _fake_parsed_game(2024)
    parsed_game["events"] = [
        GameEvent(
            game_id=parsed_game["game"].game_id,
            season_year=2024,
            event_type="goal",
            clock="10:00",
            team="Team A",
            player="Test Player",
            description=description,
        )
        for description in descriptions
    ]
    return parsed_game


def _assert_events_survive_save_and_merge(tmp_path, descriptions: list[str]) -> None:
    season_out = save_season(
        [_fake_parsed_game_with_events(descriptions)],
        2024,
        school_abbrev="FHSU",
    )
    saved = pd.read_parquet(season_out / "events.parquet")

    merged_out = merge_all_seasons(school_abbrev="FHSU")
    merged = pd.read_parquet(merged_out / "events.parquet")

    assert len(saved) == len(descriptions)
    assert saved["event_id"].nunique() == len(descriptions)
    assert len(merged) == len(descriptions)
    assert merged["event_id"].nunique() == len(descriptions)


def test_save_season_creates_parquets(tmp_path, monkeypatch):
    """save_season should create four parquet files with season_year column."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data" / "structured" / "2099").mkdir(parents=True)

    save_season([_fake_parsed_game(2099)], 2099)

    out = tmp_path / "data" / "structured" / "2099"
    for name in ("games", "player_stats", "events", "team_stats"):
        pq = out / f"{name}.parquet"
        assert pq.exists(), f"{pq} not created"

    games = pd.read_parquet(out / "games.parquet")
    assert "season_year" in games.columns
    assert int(games["season_year"].iloc[0]) == 2099

    events = pd.read_parquet(out / "events.parquet")
    assert "event_id" in events.columns
    assert "season_year" in events.columns


def test_merge_all_seasons_preserves_archive_for_single_year_request(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_season([_fake_parsed_game(2024)], 2024, school_abbrev="FHSU")
    save_season([_fake_parsed_game(2025)], 2025, school_abbrev="FHSU")

    out = merge_all_seasons([2025], school_abbrev="FHSU")
    games = pd.read_parquet(out / "games.parquet")

    assert set(games["season_year"]) == {2024, 2025}


def test_merge_all_seasons_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    save_season([_fake_parsed_game(2024)], 2024, school_abbrev="FHSU")
    save_season([_fake_parsed_game(2025)], 2025, school_abbrev="FHSU")

    out = merge_all_seasons([2025], school_abbrev="FHSU")
    initial_count = len(pd.read_parquet(out / "games.parquet"))

    merge_all_seasons([2025], school_abbrev="FHSU")
    final_count = len(pd.read_parquet(out / "games.parquet"))

    assert final_count == initial_count


def test_merge_preserves_same_clock_events_with_different_descriptions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    _assert_events_survive_save_and_merge(tmp_path, ["Header", "Penalty kick"])


def test_merge_preserves_identical_same_clock_events(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    _assert_events_survive_save_and_merge(tmp_path, ["Header", "Header"])
