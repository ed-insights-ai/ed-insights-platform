import pytest
from datetime import date

from src.models import Game, PlayerGameStats, School


@pytest.fixture()
async def seed_player_profile(db):
    """Seed data for player profile tests: school, games, player stats."""
    school = School(
        id=10,
        name="Harding",
        abbreviation="HU",
        conference="GAC",
        mascot="Bisons",
        gender="men",
    )
    school2 = School(
        id=11,
        name="Ouachita Baptist",
        abbreviation="OBU",
        conference="GAC",
        mascot="Tigers",
        gender="men",
    )
    db.add_all([school, school2])
    await db.commit()

    g1 = Game(
        game_id=5001,
        school_id=10,
        season_year=2024,
        date=date(2024, 9, 1),
        home_team="Harding",
        away_team="Ouachita Baptist",
        home_score=3,
        away_score=1,
    )
    g2 = Game(
        game_id=5002,
        school_id=10,
        season_year=2024,
        date=date(2024, 9, 8),
        home_team="Harding",
        away_team="Rogers State",
        home_score=2,
        away_score=0,
    )
    g3 = Game(
        game_id=5003,
        school_id=10,
        season_year=2023,
        date=date(2023, 9, 5),
        home_team="Harding",
        away_team="Ouachita Baptist",
        home_score=1,
        away_score=2,
    )
    # OBU game for conference average calculation
    g4 = Game(
        game_id=5004,
        school_id=11,
        season_year=2024,
        date=date(2024, 9, 1),
        home_team="Harding",
        away_team="Ouachita Baptist",
        home_score=3,
        away_score=1,
    )
    db.add_all([g1, g2, g3, g4])
    await db.commit()

    # Player stats across games
    stats = [
        PlayerGameStats(
            game_id=5001, school_id=10, player_name="Test Player",
            position="F", is_starter=True, minutes=90,
            shots=5, shots_on_goal=3, goals=2, assists=1,
        ),
        PlayerGameStats(
            game_id=5002, school_id=10, player_name="Test Player",
            position="F", is_starter=True, minutes=90,
            shots=4, shots_on_goal=2, goals=1, assists=0,
        ),
        PlayerGameStats(
            game_id=5003, school_id=10, player_name="Test Player",
            position="F", is_starter=True, minutes=85,
            shots=3, shots_on_goal=1, goals=1, assists=1,
        ),
        # Another player for conference percentile comparison
        PlayerGameStats(
            game_id=5001, school_id=10, player_name="Other Player",
            position="M", is_starter=True, minutes=90,
            shots=2, shots_on_goal=1, goals=0, assists=0,
        ),
        PlayerGameStats(
            game_id=5002, school_id=10, player_name="Other Player",
            position="M", is_starter=True, minutes=90,
            shots=1, shots_on_goal=0, goals=0, assists=1,
        ),
        PlayerGameStats(
            game_id=5003, school_id=10, player_name="Other Player",
            position="M", is_starter=False, minutes=45,
            shots=1, shots_on_goal=1, goals=0, assists=0,
        ),
        # OBU player
        PlayerGameStats(
            game_id=5004, school_id=11, player_name="OBU Player",
            position="F", is_starter=True, minutes=90,
            shots=3, shots_on_goal=2, goals=1, assists=0,
        ),
    ]
    db.add_all(stats)
    await db.commit()


@pytest.mark.anyio
async def test_player_profile_basic(client, seed_player_profile):
    """Profile endpoint returns career, seasons, game log."""
    resp = await client.get(
        "/api/players/profile",
        params={"school": "HU", "name": "Test Player"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["player_name"] == "Test Player"
    assert data["school_abbreviation"] == "HU"
    assert data["school_name"] == "Harding"
    assert data["gender"] == "men"

    # Career totals
    career = data["career"]
    assert career["seasons"] == 2
    assert career["goals"] == 4
    assert career["assists"] == 2
    assert career["shots"] == 12

    # Seasons (newest first)
    assert len(data["seasons"]) == 2
    assert data["seasons"][0]["season_year"] == 2024
    assert data["seasons"][0]["goals"] == 3
    assert data["seasons"][1]["season_year"] == 2023

    # Game log defaults to most recent season (2024)
    assert len(data["game_log"]) == 2
    assert all(g["game_id"] in [5001, 5002] for g in data["game_log"])


@pytest.mark.anyio
async def test_player_profile_specific_season(client, seed_player_profile):
    """Can request a specific season."""
    resp = await client.get(
        "/api/players/profile",
        params={"school": "HU", "name": "Test Player", "season": 2023},
    )
    assert resp.status_code == 200
    data = resp.json()
    # Game log should have 2023 games only
    assert len(data["game_log"]) == 1
    assert data["game_log"][0]["game_id"] == 5003


@pytest.mark.anyio
async def test_player_profile_not_found(client, seed_player_profile):
    """Returns 404 for nonexistent player."""
    resp = await client.get(
        "/api/players/profile",
        params={"school": "HU", "name": "Nobody"},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_player_profile_bad_school(client, seed_player_profile):
    """Returns 404 for nonexistent school."""
    resp = await client.get(
        "/api/players/profile",
        params={"school": "FAKE", "name": "Test Player"},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_player_profile_conf_averages(client, seed_player_profile):
    """Conference averages are computed."""
    resp = await client.get(
        "/api/players/profile",
        params={"school": "HU", "name": "Test Player", "season": 2024},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["conf_averages"] is not None
    assert data["conf_averages"]["season_year"] == 2024
    assert data["conf_averages"]["goals_per_game"] > 0


@pytest.mark.anyio
async def test_player_profile_kpi_calculations(client, seed_player_profile):
    """Verify per-90 and conversion calculations."""
    resp = await client.get(
        "/api/players/profile",
        params={"school": "HU", "name": "Test Player", "season": 2024},
    )
    data = resp.json()
    s = data["seasons"][0]  # 2024 season
    assert s["goals"] == 3
    assert s["shots"] == 9
    # Shot conversion: 3/9 * 100 = 33.3%
    assert abs(s["shot_conversion"] - 33.3) < 0.2
    # Goals per 90: 3 / (180/90) = 1.5
    assert abs(s["goals_per_90"] - 1.5) < 0.1
