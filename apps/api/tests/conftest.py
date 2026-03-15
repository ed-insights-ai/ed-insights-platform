import os

# Set DATABASE_URL before any src imports so the module-level engine in
# src/database.py doesn't try to connect to a real database.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from datetime import date  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import event  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

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


@pytest.fixture(params=["asyncio"])
def anyio_backend(request):
    """Only run async tests under asyncio (aiosqlite requires it)."""
    return request.param

# aiosqlite in-memory with StaticPool so the same connection is reused.
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def db():
    """Create all tables, yield a session, then drop everything."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def override_get_db(db):
    """Override the FastAPI get_db dependency to use the test session."""

    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
async def client():
    """httpx AsyncClient wired to the ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# --------------- seed helpers ---------------


@pytest.fixture()
async def seed_schools(db):
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
    await db.commit()
    return s1, s2


@pytest.fixture()
async def seed_games(db, seed_schools):
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
    await db.commit()
    return g1, g2, g3


@pytest.fixture()
async def seed_team_stats(db, seed_games):
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
    await db.commit()
    return home, away


@pytest.fixture()
async def seed_player_stats(db, seed_games):
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
    await db.commit()
    return p1, p2


@pytest.fixture()
async def seed_events(db, seed_games):
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
    await db.commit()
    return [ev]
