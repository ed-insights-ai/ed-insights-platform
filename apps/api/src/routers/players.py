from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Game, PlayerGameStats, School
from src.schemas import (
    PlayerProfile,
    PlayerProfileCareer,
    PlayerProfileConfAverages,
    PlayerProfileGameLog,
    PlayerProfileRadar,
    PlayerProfileSeason,
)

router = APIRouter(prefix="/api/players")


@router.get("/profile", response_model=PlayerProfile)
async def player_profile(
    school: str = Query(..., description="School abbreviation"),
    name: str = Query(..., description="Player name"),
    season: int | None = Query(None, description="Season year (default: most recent)"),
    db: AsyncSession = Depends(get_db),
):
    # Look up school
    row = await db.execute(select(School).where(School.abbreviation == school))
    school_obj = row.scalars().first()
    if not school_obj:
        raise HTTPException(status_code=404, detail=f"School '{school}' not found")

    school_id = school_obj.id

    # Verify player exists
    exists = await db.execute(
        select(PlayerGameStats.id)
        .where(PlayerGameStats.school_id == school_id)
        .where(PlayerGameStats.player_name == name)
        .limit(1)
    )
    if not exists.scalars().first():
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found at {school}")

    # Per-season aggregation
    season_stmt = (
        select(
            Game.season_year,
            func.count(func.distinct(PlayerGameStats.game_id)).label("games_played"),
            func.coalesce(func.sum(PlayerGameStats.goals), 0).label("goals"),
            func.coalesce(func.sum(PlayerGameStats.assists), 0).label("assists"),
            func.coalesce(func.sum(PlayerGameStats.shots), 0).label("shots"),
            func.coalesce(func.sum(PlayerGameStats.shots_on_goal), 0).label("shots_on_goal"),
            func.coalesce(func.sum(PlayerGameStats.minutes), 0).label("minutes"),
        )
        .join(Game, PlayerGameStats.game_id == Game.game_id)
        .where(PlayerGameStats.school_id == school_id)
        .where(PlayerGameStats.player_name == name)
        .group_by(Game.season_year)
        .order_by(Game.season_year.desc())
    )
    season_rows = (await db.execute(season_stmt)).all()

    if not season_rows:
        raise HTTPException(status_code=404, detail="No stats found for this player")

    # Build season objects
    seasons_data: list[PlayerProfileSeason] = []
    for r in season_rows:
        gp = r.games_played
        goals = r.goals
        shots = r.shots
        sog = r.shots_on_goal
        total_min = r.minutes

        if total_min > 0:
            goals_per_90 = round(goals / (total_min / 90), 2)
        elif gp > 0:
            goals_per_90 = round(goals / gp, 2)
        else:
            goals_per_90 = 0.0

        shot_conversion = round((goals / shots * 100), 1) if shots > 0 else 0.0
        sog_accuracy = round((sog / shots * 100), 1) if shots > 0 else 0.0

        seasons_data.append(
            PlayerProfileSeason(
                season_year=r.season_year,
                games_played=gp,
                goals=goals,
                assists=r.assists,
                shots=shots,
                shots_on_goal=sog,
                goals_per_90=goals_per_90,
                shot_conversion=shot_conversion,
                sog_accuracy=sog_accuracy,
            )
        )

    # Career summary
    career = PlayerProfileCareer(
        seasons=len(seasons_data),
        games_played=sum(s.games_played for s in seasons_data),
        goals=sum(s.goals for s in seasons_data),
        assists=sum(s.assists for s in seasons_data),
        shots=sum(s.shots for s in seasons_data),
        shots_on_goal=sum(s.shots_on_goal for s in seasons_data),
    )

    # Determine selected season
    available_years = [s.season_year for s in seasons_data]
    if season is None or season not in available_years:
        season = available_years[0]  # most recent

    # Game log for selected season
    game_log_stmt = (
        select(
            PlayerGameStats.game_id,
            Game.date,
            Game.home_team,
            Game.away_team,
            Game.home_score,
            Game.away_score,
            PlayerGameStats.goals,
            PlayerGameStats.assists,
            PlayerGameStats.shots,
            PlayerGameStats.shots_on_goal,
            PlayerGameStats.minutes,
            PlayerGameStats.is_starter,
        )
        .join(Game, PlayerGameStats.game_id == Game.game_id)
        .where(PlayerGameStats.school_id == school_id)
        .where(PlayerGameStats.player_name == name)
        .where(Game.season_year == season)
        .order_by(Game.date.desc())
    )
    game_log_rows = (await db.execute(game_log_stmt)).all()

    game_log: list[PlayerProfileGameLog] = []
    school_name_lower = school_obj.name.lower()
    for g in game_log_rows:
        is_home = (g.home_team or "").lower().startswith(school_name_lower[:4])
        opponent = g.away_team if is_home else g.home_team
        home_away = "H" if is_home else "A"
        hs = g.home_score or 0
        aws = g.away_score or 0
        school_score = hs if is_home else aws
        opp_score = aws if is_home else hs
        if school_score > opp_score:
            result = "W"
        elif school_score < opp_score:
            result = "L"
        else:
            result = "D"

        game_log.append(
            PlayerProfileGameLog(
                game_id=g.game_id,
                date=g.date,
                opponent=opponent or "Unknown",
                home_away=home_away,
                result=result,
                score=f"{school_score}-{opp_score}",
                goals=g.goals or 0,
                assists=g.assists or 0,
                shots=g.shots or 0,
                shots_on_goal=g.shots_on_goal or 0,
                minutes=g.minutes or 0,
                is_starter=g.is_starter or False,
            )
        )

    # Conference averages for selected season
    conf_averages = None
    if school_obj.conference and school_obj.gender:
        # Per-player aggregation for conference averages
        conf_player_stmt = (
            select(
                PlayerGameStats.player_name,
                PlayerGameStats.school_id,
                func.count(func.distinct(PlayerGameStats.game_id)).label("gp"),
                func.coalesce(func.sum(PlayerGameStats.goals), 0).label("goals"),
                func.coalesce(func.sum(PlayerGameStats.assists), 0).label("assists"),
                func.coalesce(func.sum(PlayerGameStats.shots), 0).label("shots"),
                func.coalesce(func.sum(PlayerGameStats.shots_on_goal), 0).label("sog"),
            )
            .join(Game, PlayerGameStats.game_id == Game.game_id)
            .join(School, PlayerGameStats.school_id == School.id)
            .where(School.conference == school_obj.conference)
            .where(School.gender == school_obj.gender)
            .where(Game.season_year == season)
            .group_by(PlayerGameStats.player_name, PlayerGameStats.school_id)
        )
        conf_players = (await db.execute(conf_player_stmt)).all()

        if conf_players:
            total_gp = sum(p.gp for p in conf_players)
            total_goals = sum(p.goals for p in conf_players)
            total_assists = sum(p.assists for p in conf_players)
            total_shots = sum(p.shots for p in conf_players)
            total_sog = sum(p.sog for p in conf_players)

            conf_averages = PlayerProfileConfAverages(
                season_year=season,
                goals_per_game=round(total_goals / total_gp, 2) if total_gp > 0 else 0,
                shot_conversion=round(total_goals / total_shots * 100, 1) if total_shots > 0 else 0,
                sog_accuracy=round(total_sog / total_shots * 100, 1) if total_shots > 0 else 0,
                assists_per_game=round(total_assists / total_gp, 2) if total_gp > 0 else 0,
                shots_per_game=round(total_shots / total_gp, 1) if total_gp > 0 else 0,
            )

    # Radar percentiles
    radar = None
    if school_obj.conference and school_obj.gender:
        # Get all players with >= 3 games in this conference+season
        all_players_stmt = (
            select(
                PlayerGameStats.player_name,
                PlayerGameStats.school_id,
                func.count(func.distinct(PlayerGameStats.game_id)).label("gp"),
                func.coalesce(func.sum(PlayerGameStats.goals), 0).label("goals"),
                func.coalesce(func.sum(PlayerGameStats.assists), 0).label("assists"),
                func.coalesce(func.sum(PlayerGameStats.shots), 0).label("shots"),
                func.coalesce(func.sum(PlayerGameStats.shots_on_goal), 0).label("sog"),
                func.coalesce(func.sum(PlayerGameStats.minutes), 0).label("minutes"),
            )
            .join(Game, PlayerGameStats.game_id == Game.game_id)
            .join(School, PlayerGameStats.school_id == School.id)
            .where(School.conference == school_obj.conference)
            .where(School.gender == school_obj.gender)
            .where(Game.season_year == season)
            .group_by(PlayerGameStats.player_name, PlayerGameStats.school_id)
            .having(func.count(func.distinct(PlayerGameStats.game_id)) >= 3)
        )
        all_players = (await db.execute(all_players_stmt)).all()

        if all_players:
            # Compute per-game/derived metrics for each player
            metrics: dict[str, list[float]] = {
                "goals": [],
                "assists": [],
                "shots": [],
                "sog": [],
                "shot_conv": [],
            }
            player_metrics: dict[str, float] | None = None

            for p in all_players:
                g_val = p.goals / p.gp if p.gp > 0 else 0
                a_val = p.assists / p.gp if p.gp > 0 else 0
                s_val = p.shots / p.gp if p.gp > 0 else 0
                sog_val = p.sog / p.gp if p.gp > 0 else 0
                conv_val = (p.goals / p.shots * 100) if p.shots > 0 else 0

                metrics["goals"].append(g_val)
                metrics["assists"].append(a_val)
                metrics["shots"].append(s_val)
                metrics["sog"].append(sog_val)
                metrics["shot_conv"].append(conv_val)

                if p.player_name == name and p.school_id == school_id:
                    player_metrics = {
                        "goals": g_val,
                        "assists": a_val,
                        "shots": s_val,
                        "sog": sog_val,
                        "shot_conv": conv_val,
                    }

            if player_metrics:
                n = len(all_players)

                def percentile(vals: list[float], val: float) -> float:
                    below = sum(1 for v in vals if v < val)
                    equal = sum(1 for v in vals if v == val)
                    return round((below + equal * 0.5) / n * 100, 0)

                radar = PlayerProfileRadar(
                    goals_pct=percentile(metrics["goals"], player_metrics["goals"]),
                    assists_pct=percentile(metrics["assists"], player_metrics["assists"]),
                    shots_pct=percentile(metrics["shots"], player_metrics["shots"]),
                    sog_pct=percentile(metrics["sog"], player_metrics["sog"]),
                    shot_conversion_pct=percentile(
                        metrics["shot_conv"], player_metrics["shot_conv"]
                    ),
                )

    return PlayerProfile(
        player_name=name,
        school_abbreviation=school_obj.abbreviation,
        school_name=school_obj.name,
        gender=school_obj.gender or "men",
        career=career,
        seasons=seasons_data,
        game_log=game_log,
        conf_averages=conf_averages,
        radar=radar,
    )
