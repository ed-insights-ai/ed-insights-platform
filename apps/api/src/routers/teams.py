from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Game, School, PlayerGameStats, TeamGameStats
from src.schemas import TeamProfile, TeamProfileSeason, TeamProfileKPIs, TeamProfileGameResult, TeamProfileTopScorer, FormResult

router = APIRouter(prefix="/api/teams")

STOP_WORDS = {"university", "college", "state", "of", "the", "and", "at", "women", "lady"}


def _ilike_pattern(school_name: str) -> str:
    for word in school_name.split():
        cleaned = word.strip("()").lower()
        if len(cleaned) >= 4 and cleaned not in STOP_WORDS:
            return f"%{word.strip('()')}%"
    return f"%{school_name.split()[0]}%"


def _matches_pattern(team_name: str | None, pattern: str) -> bool:
    if not team_name:
        return False
    keyword = pattern.strip("%").lower()
    return keyword in team_name.lower()


@router.get("/{abbr}/profile", response_model=TeamProfile)
async def team_profile(
    abbr: str,
    season: int | None = Query(None, description="Season year; defaults to most recent"),
    db: AsyncSession = Depends(get_db),
) -> TeamProfile:
    # 1. Find the school
    result = await db.execute(
        select(School).where(School.abbreviation == abbr, School.enabled == True)  # noqa: E712
    )
    school = result.scalars().first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    # 2. Available seasons
    seasons_result = await db.execute(
        select(distinct(Game.season_year)).where(
            Game.school_id == school.id,
            Game.home_score.is_not(None),
            Game.away_score.is_not(None),
        ).order_by(Game.season_year.desc())
    )
    available_seasons = [row[0] for row in seasons_result.all()]
    if not available_seasons:
        raise HTTPException(status_code=404, detail="No season data found")

    if season is None:
        season = available_seasons[0]
    elif season not in available_seasons:
        raise HTTPException(status_code=404, detail=f"No data for season {season}")

    pattern = _ilike_pattern(school.name)

    # 3. Get all scored games for this season
    games_result = await db.execute(
        select(Game).where(
            Game.school_id == school.id,
            Game.season_year == season,
            Game.home_score.is_not(None),
            Game.away_score.is_not(None),
        ).order_by(Game.date.desc())
    )
    games = games_result.scalars().all()

    # 4. Compute record
    gp = wins = losses = draws = gf = ga = 0
    clean_sheets = 0
    results_by_game: list[TeamProfileGameResult] = []

    for g in games:
        is_home = _matches_pattern(g.home_team, pattern)
        own_score = g.home_score if is_home else g.away_score
        opp_score = g.away_score if is_home else g.home_score

        gp += 1
        gf += own_score
        ga += opp_score

        if own_score > opp_score:
            wins += 1
            res = "W"
        elif own_score < opp_score:
            losses += 1
            res = "L"
        else:
            draws += 1
            res = "D"

        if opp_score == 0:
            clean_sheets += 1

        opponent = g.away_team if is_home else g.home_team
        results_by_game.append(TeamProfileGameResult(
            game_id=g.game_id,
            date=g.date,
            opponent=opponent or "Unknown",
            home_away="H" if is_home else "A",
            home_score=g.home_score,
            away_score=g.away_score,
            goals_for=own_score,
            goals_against=opp_score,
            result=res,
        ))

    points = wins * 3 + draws
    ppg = round(points / gp, 2) if gp > 0 else 0.0
    goal_diff = gf - ga

    # Form: last 5 (games already desc, take first 5, reverse)
    form: list[FormResult] = []
    for g in games[:5]:
        is_home = _matches_pattern(g.home_team, pattern)
        own_score = g.home_score if is_home else g.away_score
        opp_score = g.away_score if is_home else g.home_score
        if own_score > opp_score:
            r = "W"
        elif own_score < opp_score:
            r = "L"
        else:
            r = "D"
        form.append(FormResult(result=r, game_id=g.game_id))
    form.reverse()

    # 5. Conference rank: count schools with more points + 1
    conf_schools_result = await db.execute(
        select(School).where(
            School.conference == school.conference,
            School.gender == school.gender,
            School.enabled == True,  # noqa: E712
        )
    )
    conf_schools = conf_schools_result.scalars().all()

    schools_above = 0
    for cs in conf_schools:
        if cs.id == school.id:
            continue
        cs_pattern = _ilike_pattern(cs.name)
        cs_games_result = await db.execute(
            select(Game).where(
                Game.school_id == cs.id,
                Game.season_year == season,
                Game.home_score.is_not(None),
                Game.away_score.is_not(None),
            )
        )
        cs_games = cs_games_result.scalars().all()
        cs_wins = cs_draws = cs_gf = cs_ga = 0
        for cg in cs_games:
            cs_is_home = _matches_pattern(cg.home_team, cs_pattern)
            cs_own = cg.home_score if cs_is_home else cg.away_score
            cs_opp = cg.away_score if cs_is_home else cg.home_score
            cs_gf += cs_own
            cs_ga += cs_opp
            if cs_own > cs_opp:
                cs_wins += 1
            elif cs_own == cs_opp:
                cs_draws += 1
        cs_points = cs_wins * 3 + cs_draws
        cs_gd = cs_gf - cs_ga
        if (cs_points, cs_gd, cs_gf) > (points, goal_diff, gf):
            schools_above += 1
    conf_rank = schools_above + 1

    # 6. KPI: shot stats for this team
    tgs_result = await db.execute(
        select(TeamGameStats).join(Game, TeamGameStats.game_id == Game.game_id).where(
            TeamGameStats.school_id == school.id,
            Game.season_year == season,
            TeamGameStats.team.ilike(pattern),
        )
    )
    tgs_rows = tgs_result.scalars().all()
    total_shots = 0
    seen_games: set[int] = set()
    for row in tgs_rows:
        if row.game_id not in seen_games:
            seen_games.add(row.game_id)
            total_shots += row.shots or 0

    goals_per_game = round(gf / gp, 2) if gp > 0 else 0.0
    shot_conversion = round(gf / total_shots * 100, 1) if total_shots > 0 else 0.0
    goals_against_per_game = round(ga / gp, 2) if gp > 0 else 0.0

    # 7. Conference averages for KPI deltas
    conf_total_gpg = []
    conf_total_conv = []
    conf_total_gapg = []
    for cs in conf_schools:
        cs_pattern = _ilike_pattern(cs.name)
        cs_games_result = await db.execute(
            select(Game).where(
                Game.school_id == cs.id,
                Game.season_year == season,
                Game.home_score.is_not(None),
                Game.away_score.is_not(None),
            )
        )
        cs_games = cs_games_result.scalars().all()
        if not cs_games:
            continue
        cs_gf = cs_ga = cs_gp = 0
        for cg in cs_games:
            cs_is_home = _matches_pattern(cg.home_team, cs_pattern)
            cs_own = cg.home_score if cs_is_home else cg.away_score
            cs_opp = cg.away_score if cs_is_home else cg.home_score
            cs_gf += cs_own
            cs_ga += cs_opp
            cs_gp += 1
        if cs_gp > 0:
            conf_total_gpg.append(cs_gf / cs_gp)
            conf_total_gapg.append(cs_ga / cs_gp)

        # shots for conversion
        cs_tgs = await db.execute(
            select(TeamGameStats).join(Game, TeamGameStats.game_id == Game.game_id).where(
                TeamGameStats.school_id == cs.id,
                Game.season_year == season,
                TeamGameStats.team.ilike(cs_pattern),
            )
        )
        cs_shots = 0
        cs_seen: set[int] = set()
        for row in cs_tgs.scalars().all():
            if row.game_id not in cs_seen:
                cs_seen.add(row.game_id)
                cs_shots += row.shots or 0
        if cs_shots > 0:
            conf_total_conv.append(cs_gf / cs_shots * 100)

    conf_avg_gpg = round(sum(conf_total_gpg) / len(conf_total_gpg), 2) if conf_total_gpg else 0.0
    conf_avg_conv = round(sum(conf_total_conv) / len(conf_total_conv), 1) if conf_total_conv else 0.0
    conf_avg_gapg = round(sum(conf_total_gapg) / len(conf_total_gapg), 2) if conf_total_gapg else 0.0

    kpis = TeamProfileKPIs(
        goals_per_game=goals_per_game,
        goals_per_game_delta=round(goals_per_game - conf_avg_gpg, 2),
        shot_conversion=shot_conversion,
        shot_conversion_delta=round(shot_conversion - conf_avg_conv, 1),
        goals_against_per_game=goals_against_per_game,
        goals_against_per_game_delta=round(goals_against_per_game - conf_avg_gapg, 2),
        clean_sheets=clean_sheets,
        conf_avg_goals_per_game=conf_avg_gpg,
        conf_avg_shot_conversion=conf_avg_conv,
        conf_avg_goals_against_per_game=conf_avg_gapg,
    )

    # 8. Top scorers
    scorer_result = await db.execute(
        select(
            PlayerGameStats.player_name,
            func.sum(PlayerGameStats.goals).label("total_goals"),
            func.sum(PlayerGameStats.assists).label("total_assists"),
            func.count(distinct(PlayerGameStats.game_id)).label("games_played"),
        )
        .join(Game, PlayerGameStats.game_id == Game.game_id)
        .where(
            PlayerGameStats.school_id == school.id,
            Game.season_year == season,
        )
        .group_by(PlayerGameStats.player_name)
        .having(func.sum(PlayerGameStats.goals) > 0)
        .order_by(func.sum(PlayerGameStats.goals).desc())
        .limit(5)
    )
    top_scorers = []
    for row in scorer_result.all():
        g_played = row.games_played
        goals = row.total_goals
        top_scorers.append(TeamProfileTopScorer(
            player_name=row.player_name,
            goals=goals,
            assists=row.total_assists,
            games_played=g_played,
            goals_per_game=round(goals / g_played, 2) if g_played > 0 else 0.0,
        ))

    season_data = TeamProfileSeason(
        year=season,
        games_played=gp,
        wins=wins,
        losses=losses,
        draws=draws,
        goals_for=gf,
        goals_against=ga,
        goal_diff=goal_diff,
        points=points,
        ppg=ppg,
        form=form,
        conf_rank=conf_rank,
    )

    return TeamProfile(
        abbreviation=school.abbreviation,
        name=school.name,
        mascot=school.mascot or "",
        gender=school.gender or "men",
        conference=school.conference or "",
        season=season_data,
        kpis=kpis,
        results_by_game=results_by_game,
        top_scorers=top_scorers,
        available_seasons=available_seasons,
    )
