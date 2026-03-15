from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, literal_column
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import Game, PlayerGameStats, School, TeamGameStats
from src.schemas import PaginatedPlayers, PlayerLeaderboard, TeamStatsAggregation

router = APIRouter(prefix="/api/stats")


@router.get("/team", response_model=list[TeamStatsAggregation])
def team_stats(
    school: str | None = Query(None, description="School abbreviation"),
    season: int | None = Query(None, description="Season year"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            TeamGameStats.school_id,
            School.name.label("school_name"),
            func.count(func.distinct(TeamGameStats.game_id)).label("games_played"),
            func.coalesce(func.sum(TeamGameStats.goals), 0).label("total_goals"),
            func.coalesce(func.sum(TeamGameStats.shots), 0).label("total_shots"),
            func.coalesce(func.sum(TeamGameStats.shots_on_goal), 0).label("total_shots_on_goal"),
            func.coalesce(func.sum(TeamGameStats.corners), 0).label("total_corners"),
            func.coalesce(func.sum(TeamGameStats.saves), 0).label("total_saves"),
        )
        .join(School, TeamGameStats.school_id == School.id)
    )

    if school:
        school_row = db.query(School).filter(School.abbreviation == school).first()
        if not school_row:
            raise HTTPException(status_code=404, detail=f"School '{school}' not found")
        query = query.filter(TeamGameStats.school_id == school_row.id)

    if season:
        query = query.join(Game, TeamGameStats.game_id == Game.game_id).filter(
            Game.season_year == season
        )

    query = query.group_by(TeamGameStats.school_id, School.name)

    rows = query.all()

    return [
        TeamStatsAggregation(
            school_id=r.school_id,
            school_name=r.school_name,
            season_year=season or 0,
            games_played=r.games_played,
            total_goals=r.total_goals,
            total_shots=r.total_shots,
            total_shots_on_goal=r.total_shots_on_goal,
            total_corners=r.total_corners,
            total_saves=r.total_saves,
        )
        for r in rows
    ]


@router.get("/players", response_model=PaginatedPlayers)
def player_leaderboard(
    school: str | None = Query(None, description="School abbreviation"),
    season: int | None = Query(None, description="Season year"),
    sort: str = Query("goals", description="Sort by: goals, assists, shots, minutes"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    sort_columns = {
        "goals": "total_goals",
        "assists": "total_assists",
        "shots": "total_shots",
        "minutes": "total_minutes",
    }
    if sort not in sort_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort field. Must be one of: {', '.join(sort_columns)}",
        )

    query = (
        db.query(
            PlayerGameStats.player_name,
            PlayerGameStats.school_id,
            School.name.label("school_name"),
            func.count(func.distinct(PlayerGameStats.game_id)).label("games_played"),
            func.coalesce(func.sum(PlayerGameStats.goals), 0).label("total_goals"),
            func.coalesce(func.sum(PlayerGameStats.assists), 0).label("total_assists"),
            func.coalesce(func.sum(PlayerGameStats.shots), 0).label("total_shots"),
            func.coalesce(func.sum(PlayerGameStats.shots_on_goal), 0).label("total_shots_on_goal"),
            func.coalesce(func.sum(PlayerGameStats.minutes), 0).label("total_minutes"),
        )
        .join(School, PlayerGameStats.school_id == School.id)
    )

    if school:
        school_row = db.query(School).filter(School.abbreviation == school).first()
        if not school_row:
            raise HTTPException(status_code=404, detail=f"School '{school}' not found")
        query = query.filter(PlayerGameStats.school_id == school_row.id)

    if season:
        query = query.join(Game, PlayerGameStats.game_id == Game.game_id).filter(
            Game.season_year == season
        )

    query = query.group_by(
        PlayerGameStats.player_name,
        PlayerGameStats.school_id,
        School.name,
    )

    # Get total count before pagination
    count_query = query.subquery()
    total = db.query(func.count()).select_from(count_query).scalar()

    # Apply sort and pagination
    sort_col = sort_columns[sort]
    rows = query.order_by(desc(literal_column(sort_col))).offset(offset).limit(limit).all()

    items = [
        PlayerLeaderboard(
            player_name=r.player_name,
            school_id=r.school_id,
            school_name=r.school_name,
            games_played=r.games_played,
            total_goals=r.total_goals,
            total_assists=r.total_assists,
            total_shots=r.total_shots,
            total_shots_on_goal=r.total_shots_on_goal,
            total_minutes=r.total_minutes,
        )
        for r in rows
    ]

    return PaginatedPlayers(items=items, total=total, limit=limit, offset=offset)
