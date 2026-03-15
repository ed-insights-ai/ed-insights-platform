from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from src.database import get_db
from src.models import Game, School
from src.schemas import GameDetail, GameSummary, PaginatedGames

router = APIRouter(prefix="/api")


@router.get("/games", response_model=PaginatedGames)
def list_games(
    school: str | None = Query(None, description="School abbreviation (e.g. HU)"),
    season: int | None = Query(None, description="Season year (e.g. 2024)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Game)

    if school:
        school_row = (
            db.query(School).filter(School.abbreviation == school).first()
        )
        if not school_row:
            raise HTTPException(status_code=404, detail=f"School '{school}' not found")
        query = query.filter(Game.school_id == school_row.id)

    if season:
        query = query.filter(Game.season_year == season)

    total = query.count()
    items = query.order_by(Game.date.desc()).offset(offset).limit(limit).all()

    return PaginatedGames(items=items, total=total, limit=limit, offset=offset)


@router.get("/games/{game_id}", response_model=GameDetail)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = (
        db.query(Game)
        .options(
            joinedload(Game.team_stats),
            joinedload(Game.player_stats),
            joinedload(Game.events),
        )
        .filter(Game.game_id == game_id)
        .first()
    )
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game
