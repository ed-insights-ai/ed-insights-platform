"""Tests for the SideArm box score parser using fixture HTML."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.sidearm_parser import (
    _normalize_name,
    _strip_jersey_prefix,
    parse_sidearm_game,
)

FIXTURE = Path("tests/fixtures/sidearm_boxscore_6126.html")
FIXTURE_2016 = Path("tests/fixtures/sidearm_boxscore_2439_2016.html")


@pytest.fixture
def parsed_game():
    html = FIXTURE.read_text(encoding="utf-8")
    return parse_sidearm_game(html, game_id=302501, source_url="http://test/6126", season_year=2025)


class TestNameNormalization:
    def test_last_first_to_first_last(self):
        assert _normalize_name("Lovoy, James") == "James Lovoy"

    def test_already_first_last(self):
        assert _normalize_name("James Lovoy") == "James Lovoy"

    def test_accented_name(self):
        assert _normalize_name("Bölk, Philip") == "Philip Bölk"

    def test_compound_last_name(self):
        assert _normalize_name("Garcia Gomez, Robert") == "Robert Garcia Gomez"


class TestJerseyPrefixStrip:
    def test_strips_number(self):
        assert _strip_jersey_prefix("3 Lovoy, James") == "Lovoy, James"

    def test_no_prefix(self):
        assert _strip_jersey_prefix("Lovoy, James") == "Lovoy, James"

    def test_two_digit_number(self):
        assert _strip_jersey_prefix("13 Murie, Isaac") == "Murie, Isaac"


class TestParseGame:
    def test_game_metadata(self, parsed_game):
        game = parsed_game["game"]
        assert game.game_id == 302501
        assert game.season_year == 2025
        assert game.home_team == "Ouachita Baptist"
        assert game.away_team == "Harding"
        assert game.home_score == 2
        assert game.away_score == 1
        assert game.date == "10/16/2025"

    def test_player_stats_count(self, parsed_game):
        players = parsed_game["player_stats"]
        home_players = [p for p in players if p.team == "Ouachita Baptist"]
        away_players = [p for p in players if p.team == "Harding"]
        # 11 starters + subs for each team (excluding totals row)
        assert len(home_players) >= 11
        assert len(away_players) >= 11

    def test_player_names_normalized(self, parsed_game):
        players = parsed_game["player_stats"]
        names = [p.player_name for p in players]
        # Should be "First Last", not "Last, First"
        assert "James Lovoy" in names
        assert "Xavier O'Dwyer" in names
        assert "Rinner Stewart" in names

    def test_starters_vs_subs(self, parsed_game):
        players = parsed_game["player_stats"]
        home_players = [p for p in players if p.team == "Ouachita Baptist"]
        starters = [p for p in home_players if p.is_starter]
        subs = [p for p in home_players if not p.is_starter]
        assert len(starters) == 11
        assert len(subs) >= 1

    def test_player_stats_values(self, parsed_game):
        players = parsed_game["player_stats"]
        lovoy = next(p for p in players if p.player_name == "James Lovoy")
        assert lovoy.jersey_number == 3
        assert lovoy.position == "DEF"
        assert lovoy.shots == 2
        assert lovoy.shots_on_goal == 1
        assert lovoy.goals == 1
        assert lovoy.assists == 0
        assert lovoy.minutes == 90
        assert lovoy.is_starter is True

    def test_team_stats(self, parsed_game):
        team_stats = parsed_game["team_stats"]
        assert len(team_stats) == 2

        home = next(t for t in team_stats if t.is_home)
        away = next(t for t in team_stats if not t.is_home)

        assert home.team == "Ouachita Baptist"
        assert home.shots == 9
        assert home.shots_on_goal == 4
        assert home.corners == 3
        assert home.saves == 5
        assert home.goals == 2

        assert away.team == "Harding"
        assert away.shots == 15
        assert away.shots_on_goal == 6
        assert away.corners == 2
        assert away.saves == 2
        assert away.goals == 1

    def test_goal_events(self, parsed_game):
        goals = [e for e in parsed_game["events"] if e.event_type == "goal"]
        assert len(goals) == 3

        # First goal: 14:33 OBU James Lovoy
        g1 = goals[0]
        assert g1.clock == "14:33"
        assert g1.team == "Ouachita Baptist"
        assert "Lovoy" in g1.player
        assert g1.assist1 is not None
        assert "Tice" in g1.assist1

    def test_caution_events(self, parsed_game):
        cards = [e for e in parsed_game["events"] if "card" in e.event_type]
        assert len(cards) == 5
        # All should be yellow cards
        assert all(c.event_type == "yellow_card" for c in cards)

    def test_abbrev_map(self, parsed_game):
        abbrev = parsed_game["abbrev_map"]
        assert abbrev["OBU"] == "Ouachita Baptist"
        assert abbrev["HU"] == "Harding"

    def test_events_sorted_by_time(self, parsed_game):
        events = parsed_game["events"]
        times = [e.clock for e in events]
        # Convert to seconds for comparison
        def to_sec(t):
            parts = t.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        secs = [to_sec(t) for t in times]
        assert secs == sorted(secs)


class TestParseGame2016:
    """Test parsing a 2016 SideArm box score with different table layout."""

    @pytest.fixture
    def parsed_game_2016(self):
        html = FIXTURE_2016.read_text(encoding="utf-8")
        return parse_sidearm_game(html, game_id=320160, source_url="http://test/2439", season_year=2016)

    def test_game_metadata(self, parsed_game_2016):
        game = parsed_game_2016["game"]
        assert game.game_id == 320160
        assert game.season_year == 2016
        assert game.date == "9/6/2016"
        assert game.home_score == 0
        assert game.away_score == 2

    def test_teams_identified(self, parsed_game_2016):
        game = parsed_game_2016["game"]
        # In 2016 fixture, Dallas Baptist is listed first (away), Ouachita second (home)
        assert "Dallas Baptist" in game.home_team or "Dallas Baptist" in game.away_team
        assert "Ouachita" in game.home_team or "Ouachita" in game.away_team

    def test_player_stats_found(self, parsed_game_2016):
        players = parsed_game_2016["player_stats"]
        assert len(players) >= 20  # Both teams should have players

    def test_player_names_normalized(self, parsed_game_2016):
        players = parsed_game_2016["player_stats"]
        names = [p.player_name for p in players]
        # 2016 fixture has "Tyler Hoffman" (already First Last in the raw data)
        assert "Tyler Hoffman" in names

    def test_goal_events(self, parsed_game_2016):
        goals = [e for e in parsed_game_2016["events"] if e.event_type == "goal"]
        assert len(goals) == 2

    def test_no_cautions_graceful(self, parsed_game_2016):
        """2016 fixture has no cautions table — parser should handle gracefully."""
        # Should not crash; cards list may be empty
        cards = [e for e in parsed_game_2016["events"] if "card" in e.event_type]
        assert isinstance(cards, list)

    def test_team_stats(self, parsed_game_2016):
        team_stats = parsed_game_2016["team_stats"]
        assert len(team_stats) == 2
