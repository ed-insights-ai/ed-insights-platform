from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db
from src.models import Game, School
from src.schemas import GameDetail, PaginatedGames

router = APIRouter(prefix="/api")


@router.get("/games", response_model=PaginatedGames)
async def list_games(
    school: str | None = Query(None, description="School abbreviation (e.g. HU)"),
    school_id: int | None = Query(
        None, description="School ID (alternative to abbreviation)"
    ),
    season: int | None = Query(None, description="Season year (e.g. 2024)"),
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Game)

    if school:
        row = await db.execute(select(School).where(School.abbreviation == school))
        school_row = row.scalars().first()
        if not school_row:
            raise HTTPException(status_code=404, detail=f"School '{school}' not found")
        stmt = stmt.where(Game.school_id == school_row.id)
    elif school_id:
        stmt = stmt.where(Game.school_id == school_id)

    if season:
        stmt = stmt.where(Game.season_year == season)

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar()

    result = await db.execute(
        stmt.order_by(Game.date.desc()).offset(offset).limit(limit)
    )
    items = result.scalars().all()

    return PaginatedGames(items=items, total=total, limit=limit, offset=offset)


@router.get("/games/{game_id}", response_model=GameDetail)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game)
        .options(
            joinedload(Game.team_stats),
            joinedload(Game.player_stats),
            joinedload(Game.events),
        )
        .where(Game.game_id == game_id)
    )
    game = result.unique().scalars().first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
