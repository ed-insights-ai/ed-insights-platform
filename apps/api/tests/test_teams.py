import pytest
from datetime import date

from src.models import Game, PlayerGameStats, School, TeamGameStats


@pytest.fixture()
async def seed_team_profile(db):
    """Seed data for team profile tests."""
    school = School(
        id=20,
        name="Fort Hays State",
        abbreviation="FHSU",
        conference="GAC",
        mascot="Tigers",
        gender="men",
    )
    school2 = School(
        id=21,
        name="Rogers State",
        abbreviation="RSU",
        conference="GAC",
        mascot="Hillcats",
        gender="men",
    )
    db.add_all([school, school2])
    await db.commit()

    # FHSU games
    g1 = Game(
        game_id=9001, school_id=20, season_year=2024,
        date=date(2024, 9, 1),
        home_team="Fort Hays State", away_team="Rogers State",
        home_score=3, away_score=1,
    )
    g2 = Game(
        game_id=9002, school_id=20, season_year=2024,
        date=date(2024, 9, 8),
        home_team="Rogers State", away_team="Fort Hays State",
        home_score=0, away_score=2,
    )
    g3 = Game(
        game_id=9003, school_id=20, season_year=2023,
        date=date(2023, 9, 5),
        home_team="Fort Hays State", away_team="Rogers State",
        home_score=1, away_score=1,
    )
    # RSU game
    g4 = Game(
        game_id=9004, school_id=21, season_year=2024,
        date=date(2024, 9, 1),
        home_team="Fort Hays State", away_team="Rogers State",
        home_score=3, away_score=1,
    )
    db.add_all([g1, g2, g3, g4])
    await db.commit()

    # Team stats for FHSU
    tgs1 = TeamGameStats(
        game_id=9001, school_id=20, team="Fort Hays State",
        is_home=True, shots=15, shots_on_goal=8, goals=3, corners=6, saves=2,
    )
    tgs2 = TeamGameStats(
        game_id=9002, school_id=20, team="Fort Hays State",
        is_home=False, shots=12, shots_on_goal=6, goals=2, corners=4, saves=0,
    )
    # RSU team stats
    tgs3 = TeamGameStats(
        game_id=9004, school_id=21, team="Rogers State",
        is_home=False, shots=10, shots_on_goal=4, goals=1, corners=3, saves=5,
    )
    db.add_all([tgs1, tgs2, tgs3])
    await db.commit()

    # Player stats for FHSU
    stats = [
        PlayerGameStats(
            game_id=9001, school_id=20, player_name="Alex Doe",
            position="F", is_starter=True, minutes=90,
            shots=6, shots_on_goal=4, goals=2, assists=0,
        ),
        PlayerGameStats(
            game_id=9001, school_id=20, player_name="Sam Lee",
            position="M", is_starter=True, minutes=90,
            shots=3, shots_on_goal=2, goals=1, assists=1,
        ),
        PlayerGameStats(
            game_id=9002, school_id=20, player_name="Alex Doe",
            position="F", is_starter=True, minutes=90,
            shots=4, shots_on_goal=3, goals=1, assists=0,
        ),
        PlayerGameStats(
            game_id=9002, school_id=20, player_name="Sam Lee",
            position="M", is_starter=True, minutes=85,
            shots=2, shots_on_goal=1, goals=1, assists=1,
        ),
    ]
    db.add_all(stats)
    await db.commit()


@pytest.mark.anyio
async def test_team_profile_basic(client, seed_team_profile):
    """Profile endpoint returns season record, KPIs, results, top scorers."""
    resp = await client.get("/api/teams/FHSU/profile", params={"season": 2024})
    assert resp.status_code == 200
    data = resp.json()

    assert data["abbreviation"] == "FHSU"
    assert data["name"] == "Fort Hays State"
    assert data["mascot"] == "Tigers"
    assert data["gender"] == "men"
    assert data["conference"] == "GAC"

    # Season record: 2 games, 2 wins, 0 losses, 0 draws
    season = data["season"]
    assert season["year"] == 2024
    assert season["games_played"] == 2
    assert season["wins"] == 2
    assert season["losses"] == 0
    assert season["draws"] == 0
    assert season["goals_for"] == 5
    assert season["goals_against"] == 1
    assert season["points"] == 6

    # Form: last 5 (or less)
    assert len(season["form"]) == 2
    assert all(f["result"] == "W" for f in season["form"])

    # Conf rank should be 1 (more points than RSU)
    assert season["conf_rank"] == 1


@pytest.mark.anyio
async def test_team_profile_kpis(client, seed_team_profile):
    """KPI values are computed correctly."""
    resp = await client.get("/api/teams/FHSU/profile", params={"season": 2024})
    data = resp.json()
    kpis = data["kpis"]

    # Goals per game: 5/2 = 2.5
    assert kpis["goals_per_game"] == 2.5
    # GA per game: 1/2 = 0.5
    assert kpis["goals_against_per_game"] == 0.5
    # Shot conversion: 5/27 * 100 = 18.5%
    assert kpis["shot_conversion"] == 18.5
    # Clean sheets: 1 (game 9002, GA=0)
    assert kpis["clean_sheets"] == 1


@pytest.mark.anyio
async def test_team_profile_top_scorers(client, seed_team_profile):
    """Top scorers are returned sorted by goals desc."""
    resp = await client.get("/api/teams/FHSU/profile", params={"season": 2024})
    data = resp.json()

    scorers = data["top_scorers"]
    assert len(scorers) == 2
    assert scorers[0]["player_name"] == "Alex Doe"
    assert scorers[0]["goals"] == 3
    assert scorers[1]["player_name"] == "Sam Lee"
    assert scorers[1]["goals"] == 2


@pytest.mark.anyio
async def test_team_profile_results(client, seed_team_profile):
    """Results by game are returned."""
    resp = await client.get("/api/teams/FHSU/profile", params={"season": 2024})
    data = resp.json()

    results = data["results_by_game"]
    assert len(results) == 2
    # Most recent first (desc)
    assert results[0]["game_id"] == 9002
    assert results[0]["result"] == "W"
    assert results[0]["home_away"] == "A"
    assert results[1]["game_id"] == 9001
    assert results[1]["result"] == "W"
    assert results[1]["home_away"] == "H"


@pytest.mark.anyio
async def test_team_profile_available_seasons(client, seed_team_profile):
    """Available seasons include all years with data."""
    resp = await client.get("/api/teams/FHSU/profile", params={"season": 2024})
    data = resp.json()
    assert 2024 in data["available_seasons"]
    assert 2023 in data["available_seasons"]


@pytest.mark.anyio
async def test_team_profile_default_season(client, seed_team_profile):
    """Without season param, defaults to most recent."""
    resp = await client.get("/api/teams/FHSU/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["season"]["year"] == 2024


@pytest.mark.anyio
async def test_team_profile_not_found(client, seed_team_profile):
    """Returns 404 for nonexistent school."""
    resp = await client.get("/api/teams/FAKE/profile")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_team_profile_bad_season(client, seed_team_profile):
    """Returns 404 for season with no data."""
    resp = await client.get("/api/teams/FHSU/profile", params={"season": 1999})
    assert resp.status_code == 404
