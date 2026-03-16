"""Tests for the Smart Insights endpoint."""

from datetime import date

import pytest

from src.models import Game, PlayerGameStats, School, TeamGameStats


# --------------- seed helpers specific to insights ---------------


@pytest.fixture()
async def school_hu(db):
    s = School(id=10, name="Harding University", abbreviation="HU", conference="GAC", mascot="Bisons")
    db.add(s)
    await db.commit()
    return s


@pytest.fixture()
async def scoring_streak_games(db, school_hu):
    """4 games where player 'Carlos Reyes' scores in the last 3."""
    games = []
    for i, (d, hs, aws) in enumerate([
        (date(2024, 9, 1), 1, 0),
        (date(2024, 9, 8), 2, 1),
        (date(2024, 9, 15), 1, 1),
        (date(2024, 9, 22), 3, 0),
    ]):
        g = Game(
            game_id=5000 + i, school_id=school_hu.id, season_year=2024,
            date=d, home_team="Harding University", away_team="Opponent",
            home_score=hs, away_score=aws,
        )
        games.append(g)
    db.add_all(games)
    await db.flush()

    # Carlos scores in games 2,3,4 (most recent 3) but not game 1
    stats = [
        PlayerGameStats(game_id=5000, school_id=10, team="Harding University",
                        player_name="Carlos Reyes", goals=0, shots=2, position="F"),
        PlayerGameStats(game_id=5001, school_id=10, team="Harding University",
                        player_name="Carlos Reyes", goals=1, shots=3, position="F"),
        PlayerGameStats(game_id=5002, school_id=10, team="Harding University",
                        player_name="Carlos Reyes", goals=1, shots=2, position="F"),
        PlayerGameStats(game_id=5003, school_id=10, team="Harding University",
                        player_name="Carlos Reyes", goals=2, shots=4, position="F"),
    ]
    db.add_all(stats)
    await db.commit()
    return games


@pytest.fixture()
async def unbeaten_run_games(db, school_hu):
    """5 games: 3W 2D — unbeaten in 5."""
    games = []
    scores = [
        (date(2024, 9, 1), 2, 0),   # W
        (date(2024, 9, 8), 1, 1),   # D
        (date(2024, 9, 15), 3, 1),  # W
        (date(2024, 9, 22), 0, 0),  # D
        (date(2024, 9, 29), 1, 0),  # W
    ]
    for i, (d, hs, aws) in enumerate(scores):
        g = Game(
            game_id=6000 + i, school_id=school_hu.id, season_year=2024,
            date=d, home_team="Harding University", away_team="Opponent",
            home_score=hs, away_score=aws,
        )
        games.append(g)
    db.add_all(games)
    await db.commit()
    return games


@pytest.fixture()
async def losing_streak_games(db, school_hu):
    """4 games, last 3 are losses."""
    games = []
    scores = [
        (date(2024, 9, 1), 2, 0),   # W
        (date(2024, 9, 8), 0, 1),   # L
        (date(2024, 9, 15), 1, 3),  # L
        (date(2024, 9, 22), 0, 2),  # L
    ]
    for i, (d, hs, aws) in enumerate(scores):
        g = Game(
            game_id=7000 + i, school_id=school_hu.id, season_year=2024,
            date=d, home_team="Harding University", away_team="Opponent",
            home_score=hs, away_score=aws,
        )
        games.append(g)
    db.add_all(games)
    await db.commit()
    return games


@pytest.fixture()
async def goal_drought_games(db, school_hu):
    """6 games, last 3 are scoreless draws (drought, not losing streak, not unbeaten run)."""
    games = []
    scores = [
        (date(2024, 9, 1), 2, 0),   # W - scored
        (date(2024, 9, 8), 1, 0),   # W - scored
        (date(2024, 9, 12), 0, 1),  # L - breaks unbeaten run
        (date(2024, 9, 15), 0, 0),  # D - drought start
        (date(2024, 9, 22), 0, 0),  # D - drought
        (date(2024, 9, 29), 0, 0),  # D - drought
    ]
    for i, (d, hs, aws) in enumerate(scores):
        g = Game(
            game_id=8000 + i, school_id=school_hu.id, season_year=2024,
            date=d, home_team="Harding University", away_team="Opponent",
            home_score=hs, away_score=aws,
        )
        games.append(g)
    db.add_all(games)
    await db.commit()
    return games


@pytest.fixture()
async def clean_sheet_split_games(db, school_hu):
    """Home: 3 clean sheets. Away: 0 clean sheets."""
    games = []
    # 3 home games with clean sheets
    for i in range(3):
        games.append(Game(
            game_id=9000 + i, school_id=school_hu.id, season_year=2024,
            date=date(2024, 9, 1 + i), home_team="Harding University",
            away_team="Opponent", home_score=1, away_score=0,
        ))
    # 3 away games, all concede
    for i in range(3):
        games.append(Game(
            game_id=9010 + i, school_id=school_hu.id, season_year=2024,
            date=date(2024, 9, 10 + i), home_team="Opponent",
            away_team="Harding University", home_score=2, away_score=1,
        ))
    db.add_all(games)
    await db.commit()
    return games


@pytest.fixture()
async def top_scorer_games(db, school_hu):
    """Top scorer with >= 0.6 goals per game."""
    games = []
    for i in range(5):
        g = Game(
            game_id=9100 + i, school_id=school_hu.id, season_year=2024,
            date=date(2024, 9, 1 + i), home_team="Harding University",
            away_team="Opponent", home_score=2, away_score=0,
        )
        games.append(g)
    db.add_all(games)
    await db.flush()

    # 4 goals in 5 games = 0.80 gpg
    stats = []
    goals_per_game = [1, 1, 0, 1, 1]
    for i, goals in enumerate(goals_per_game):
        stats.append(PlayerGameStats(
            game_id=9100 + i, school_id=10, team="Harding University",
            player_name="Maria Lopez", goals=goals, shots=3, position="F",
        ))
    db.add_all(stats)
    await db.commit()
    return games


@pytest.fixture()
async def conf_split_games(db, school_hu):
    """Conference: 0W-3L, Non-conf: 3W-0L — 100% diff."""
    games = []
    # 3 conf losses
    for i in range(3):
        games.append(Game(
            game_id=9200 + i, school_id=school_hu.id, season_year=2024,
            date=date(2024, 9, 1 + i), home_team="Harding University",
            away_team="Conf Opponent", home_score=0, away_score=1,
            is_conference_game=True,
        ))
    # 3 non-conf wins
    for i in range(3):
        games.append(Game(
            game_id=9210 + i, school_id=school_hu.id, season_year=2024,
            date=date(2024, 9, 10 + i), home_team="Harding University",
            away_team="Non-Conf Opponent", home_score=2, away_score=0,
            is_conference_game=False,
        ))
    db.add_all(games)
    await db.commit()
    return games


@pytest.fixture()
async def conversion_trend_games(db, school_hu):
    """Season avg much higher than last 5 games."""
    games = []
    team_stats_rows = []
    # 10 games total. First 5: high conversion. Last 5: low conversion.
    for i in range(10):
        g = Game(
            game_id=9300 + i, school_id=school_hu.id, season_year=2024,
            date=date(2024, 9, 1 + i), home_team="Harding University",
            away_team="Opponent", home_score=2 if i < 5 else 0, away_score=0,
        )
        games.append(g)
        # First 5: 2 goals on 10 shots (20%), Last 5: 0 goals on 10 shots (0%)
        team_stats_rows.append(TeamGameStats(
            game_id=9300 + i, school_id=10, team="Harding University",
            is_home=True, shots=10, shots_on_goal=5,
            goals=2 if i < 5 else 0, corners=3, saves=2,
        ))
    db.add_all(games)
    await db.flush()
    db.add_all(team_stats_rows)
    await db.commit()
    return games


# --------------- tests ---------------


@pytest.mark.anyio
async def test_insights_unknown_school(client):
    resp = await client.get("/api/insights?school=NOPE&season=2024")
    assert resp.status_code == 200
    assert resp.json() == {"insights": []}


@pytest.mark.anyio
async def test_insights_no_games(client, school_hu):
    resp = await client.get("/api/insights?school=HU&season=2024")
    assert resp.status_code == 200
    assert resp.json() == {"insights": []}


@pytest.mark.anyio
async def test_scoring_streak(client, scoring_streak_games):
    resp = await client.get("/api/insights?school=HU&season=2024")
    assert resp.status_code == 200
    data = resp.json()
    types = [i["type"] for i in data["insights"]]
    assert "scoring_streak" in types
    streak_insight = next(i for i in data["insights"] if i["type"] == "scoring_streak")
    assert "Carlos Reyes" in streak_insight["text"]
    assert "3 consecutive" in streak_insight["text"]


@pytest.mark.anyio
async def test_unbeaten_run(client, unbeaten_run_games):
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    types = [i["type"] for i in data["insights"]]
    assert "unbeaten_run" in types
    insight = next(i for i in data["insights"] if i["type"] == "unbeaten_run")
    assert "5 games" in insight["text"]
    assert "3W 2D" in insight["text"]


@pytest.mark.anyio
async def test_losing_streak(client, losing_streak_games):
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    types = [i["type"] for i in data["insights"]]
    assert "losing_streak" in types
    insight = next(i for i in data["insights"] if i["type"] == "losing_streak")
    assert "3 consecutive" in insight["text"]


@pytest.mark.anyio
async def test_goal_drought(client, goal_drought_games):
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    types = [i["type"] for i in data["insights"]]
    assert "goal_drought" in types
    insight = next(i for i in data["insights"] if i["type"] == "goal_drought")
    assert "4 consecutive" in insight["text"]


@pytest.mark.anyio
async def test_clean_sheet_split(client, clean_sheet_split_games):
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    types = [i["type"] for i in data["insights"]]
    assert "clean_sheet_split" in types
    insight = next(i for i in data["insights"] if i["type"] == "clean_sheet_split")
    assert "3 clean sheet" in insight["text"]
    assert "0 on the road" in insight["text"]


@pytest.mark.anyio
async def test_top_scorer_pace(client, top_scorer_games):
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    types = [i["type"] for i in data["insights"]]
    assert "top_scorer_pace" in types
    insight = next(i for i in data["insights"] if i["type"] == "top_scorer_pace")
    assert "Maria Lopez" in insight["text"]
    assert "0.80" in insight["text"]


@pytest.mark.anyio
async def test_conf_split(client, conf_split_games):
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    types = [i["type"] for i in data["insights"]]
    assert "conf_split" in types
    insight = next(i for i in data["insights"] if i["type"] == "conf_split")
    assert "struggling in conference" in insight["text"]


@pytest.mark.anyio
async def test_conversion_trend(client, conversion_trend_games):
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    types = [i["type"] for i in data["insights"]]
    assert "conversion_trend" in types
    insight = next(i for i in data["insights"] if i["type"] == "conversion_trend")
    assert "dropped" in insight["text"]


@pytest.mark.anyio
async def test_max_4_insights(client, unbeaten_run_games, school_hu, db):
    """Even with many rules firing, max 4 insights returned."""
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    assert len(data["insights"]) <= 4


@pytest.mark.anyio
async def test_only_one_streak_insight(client, losing_streak_games, school_hu, db):
    """Losing streak + goal drought shouldn't both appear (both are streak types)."""
    # Add goal drought on top of losing streak — the games already have 0 goals in last 3
    resp = await client.get("/api/insights?school=HU&season=2024")
    data = resp.json()
    streak_types = {"scoring_streak", "unbeaten_run", "losing_streak", "goal_drought"}
    streak_count = sum(1 for i in data["insights"] if i["type"] in streak_types)
    assert streak_count <= 1
