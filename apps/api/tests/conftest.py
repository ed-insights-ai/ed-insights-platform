import os

# Set DATABASE_URL before any src imports so the module-level engine in
# src/database.py doesn't choke on an empty string.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from datetime import date  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from src.database import get_db  # noqa: E402
from src.main import app  # noqa: E402
from src.models import (  # noqa: E402
    Base,
    Game,
    GameEvent,
    PlayerGameStats,
    School,
    TeamGameStats,
)

# SQLite in-memory with StaticPool so the same connection is reused across
# threads (FastAPI runs sync endpoints in a threadpool).
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def db():
    """Create all tables, yield a session, then drop everything."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_get_db(db):
    """Override the FastAPI get_db dependency to use the test session."""

    def _override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    """Starlette TestClient wired to the ASGI app."""
    return TestClient(app)


# --------------- seed helpers ---------------


@pytest.fixture()
def seed_schools(db):
    """Insert two schools and flush so IDs are available."""
    s1 = School(
        id=1,
        name="Howard University",
        abbreviation="HU",
        conference="MEAC",
        mascot="Bison",
    )
    s2 = School(
        id=2, name="Morgan State", abbreviation="MSU", conference="MEAC", mascot="Bears"
    )
    db.add_all([s1, s2])
    db.commit()
    return s1, s2


@pytest.fixture()
def seed_games(db, seed_schools):
    """Insert games for both schools."""
    s1, s2 = seed_schools
    g1 = Game(
        game_id=1001,
        school_id=s1.id,
        season_year=2024,
        date=date(2024, 9, 1),
        venue="Greene Stadium",
        home_team="Howard University",
        away_team="Morgan State",
        home_score=2,
        away_score=1,
    )
    g2 = Game(
        game_id=1002,
        school_id=s1.id,
        season_year=2024,
        date=date(2024, 9, 8),
        venue="Greene Stadium",
        home_team="Howard University",
        away_team="Coppin State",
        home_score=3,
        away_score=0,
    )
    g3 = Game(
        game_id=2001,
        school_id=s2.id,
        season_year=2024,
        date=date(2024, 9, 3),
        venue="Hughes Stadium",
        home_team="Morgan State",
        away_team="Delaware State",
        home_score=1,
        away_score=1,
    )
    db.add_all([g1, g2, g3])
    db.commit()
    return g1, g2, g3


@pytest.fixture()
def seed_team_stats(db, seed_games):
    """Insert team game stats for the first game (home & away)."""
    g1, *_ = seed_games
    home = TeamGameStats(
        game_id=g1.game_id,
        school_id=1,
        team="Howard University",
        is_home=True,
        shots=12,
        shots_on_goal=6,
        goals=2,
        corners=5,
        saves=3,
    )
    away = TeamGameStats(
        game_id=g1.game_id,
        school_id=1,
        team="Morgan State",
        is_home=False,
        shots=8,
        shots_on_goal=4,
        goals=1,
        corners=3,
        saves=4,
    )
    db.add_all([home, away])
    db.commit()
    return home, away


@pytest.fixture()
def seed_player_stats(db, seed_games):
    """Insert player stats for game 1001."""
    g1, *_ = seed_games
    p1 = PlayerGameStats(
        game_id=g1.game_id,
        school_id=1,
        team="Howard University",
        jersey_number="9",
        player_name="Alice Johnson",
        position="F",
        is_starter=True,
        minutes=90,
        shots=5,
        shots_on_goal=3,
        goals=2,
        assists=0,
    )
    p2 = PlayerGameStats(
        game_id=g1.game_id,
        school_id=1,
        team="Howard University",
        jersey_number="7",
        player_name="Beth Smith",
        position="M",
        is_starter=True,
        minutes=85,
        shots=3,
        shots_on_goal=2,
        goals=0,
        assists=2,
    )
    db.add_all([p1, p2])
    db.commit()
    return p1, p2


@pytest.fixture()
def seed_events(db, seed_games):
    """Insert a game event for game 1001."""
    g1, *_ = seed_games
    ev = GameEvent(
        game_id=g1.game_id,
        school_id=1,
        event_type="goal",
        clock="23:15",
        team="Howard University",
        player="Alice Johnson",
        assist1="Beth Smith",
        description="Goal from close range",
    )
    db.add(ev)
    db.commit()
    return [ev]
