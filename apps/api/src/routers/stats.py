from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, desc, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Game, PlayerGameStats, School, TeamGameStats
from src.schemas import PaginatedPlayers, PlayerLeaderboard, TeamStatsAggregation

router = APIRouter(prefix="/api/stats")


@router.get("/team", response_model=list[TeamStatsAggregation])
async def team_stats(
    school: str | None = Query(None, description="School abbreviation"),
    season: int | None = Query(None, description="Season year"),
    db: AsyncSession = Depends(get_db),
):
    # Join Game to access season_year and to filter own-team stats.
    # Each game produces TWO team_game_stats rows (home + away); we must
    # only include the row that matches the school's own team by comparing
    # TeamGameStats.team to Game.home_team (when is_home) or away_team.
    stmt = (
        select(
            TeamGameStats.school_id,
            School.name.label("school_name"),
            Game.season_year,
            func.count(func.distinct(TeamGameStats.game_id)).label("games_played"),
            func.coalesce(func.sum(TeamGameStats.goals), 0).label("total_goals"),
            func.coalesce(func.sum(TeamGameStats.shots), 0).label("total_shots"),
            func.coalesce(func.sum(TeamGameStats.shots_on_goal), 0).label("total_shots_on_goal"),
            func.coalesce(func.sum(TeamGameStats.corners), 0).label("total_corners"),
            func.coalesce(func.sum(TeamGameStats.saves), 0).label("total_saves"),
        )
        .join(School, TeamGameStats.school_id == School.id)
        .join(Game, TeamGameStats.game_id == Game.game_id)
        .where(
            # Only include the school's own team row, not the opponent's.
            TeamGameStats.team
            == case(
                (TeamGameStats.is_home == True, Game.home_team),  # noqa: E712
                else_=Game.away_team,
            )
        )
    )

    if school:
        row = await db.execute(select(School).where(School.abbreviation == school))
        school_row = row.scalars().first()
        if not school_row:
            raise HTTPException(status_code=404, detail=f"School '{school}' not found")
        stmt = stmt.where(TeamGameStats.school_id == school_row.id)

    if season:
        stmt = stmt.where(Game.season_year == season)

    stmt = stmt.group_by(TeamGameStats.school_id, School.name, Game.season_year)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        TeamStatsAggregation(
            school_id=r.school_id,
            school_name=r.school_name,
            season_year=r.season_year,
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
async def player_leaderboard(
    school: str | None = Query(None, description="School abbreviation"),
    season: int | None = Query(None, description="Season year"),
    sort: str = Query("goals", description="Sort by: goals, assists, shots, minutes"),
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
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

    stmt = (
        select(
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
        row = await db.execute(select(School).where(School.abbreviation == school))
        school_row = row.scalars().first()
        if not school_row:
            raise HTTPException(status_code=404, detail=f"School '{school}' not found")
        stmt = stmt.where(PlayerGameStats.school_id == school_row.id)

    if season:
        stmt = stmt.join(Game, PlayerGameStats.game_id == Game.game_id).where(
            Game.season_year == season
        )

    stmt = stmt.group_by(
        PlayerGameStats.player_name,
        PlayerGameStats.school_id,
        School.name,
    )

    # Get total count before pagination
    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar()

    # Apply sort and pagination
    sort_col = sort_columns[sort]
    result = await db.execute(
        stmt.order_by(desc(literal_column(sort_col))).offset(offset).limit(limit)
    )
    rows = result.all()

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
