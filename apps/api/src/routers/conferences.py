from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Game, School
from src.schemas import ConferenceStanding, FormResult

router = APIRouter(prefix="/api/conferences")

STOP_WORDS = {"university", "college", "state", "of", "the", "and", "at", "women", "lady"}


def _ilike_pattern(school_name: str) -> str:
    """Derive ILIKE pattern from school name. Takes first significant word >= 4 chars."""
    for word in school_name.split():
        cleaned = word.strip("()").lower()
        if len(cleaned) >= 4 and cleaned not in STOP_WORDS:
            return f"%{word.strip('()')}%"
    # fallback: first word
    return f"%{school_name.split()[0]}%"


def _matches_pattern(team_name: str | None, pattern: str) -> bool:
    """Check if team_name matches the ILIKE pattern (case-insensitive substring)."""
    if not team_name:
        return False
    keyword = pattern.strip("%").lower()
    return keyword in team_name.lower()


@router.get("/{abbr}/standings", response_model=list[ConferenceStanding])
async def conference_standings(
    abbr: str,
    season: int = Query(..., description="Season year e.g. 2024"),
    gender: str = Query("men", description="'men' or 'women'"),
    db: AsyncSession = Depends(get_db),
) -> list[ConferenceStanding]:
    # 1. Get schools in this conference
    result = await db.execute(
        select(School).where(
            School.conference == abbr,
            School.gender == gender,
            School.enabled == True,  # noqa: E712
        ).order_by(School.name)
    )
    schools = result.scalars().all()

    standings: list[ConferenceStanding] = []

    for school in schools:
        pattern = _ilike_pattern(school.name)

        # 2. Get all scored games for this school this season
        games_stmt = select(Game).where(
            Game.school_id == school.id,
            Game.season_year == season,
            Game.home_score.is_not(None),
            Game.away_score.is_not(None),
        ).order_by(Game.date.desc())

        games_result = await db.execute(games_stmt)
        games = games_result.scalars().all()

        # 3. Compute standings from games table
        gp = wins = losses = draws = gf = ga = 0

        for g in games:
            is_home = _matches_pattern(g.home_team, pattern)

            own_score = g.home_score if is_home else g.away_score
            opp_score = g.away_score if is_home else g.home_score

            gp += 1
            gf += own_score
            ga += opp_score

            if own_score > opp_score:
                wins += 1
            elif own_score < opp_score:
                losses += 1
            else:
                draws += 1

        points = wins * 3 + draws
        ppg = round(points / gp, 2) if gp > 0 else 0.0
        goal_diff = gf - ga

        # 4. Form: last 5 games (games already sorted desc, take first 5, then reverse)
        form: list[FormResult] = []
        for g in games[:5]:
            is_home = _matches_pattern(g.home_team, pattern)
            own_score = g.home_score if is_home else g.away_score
            opp_score = g.away_score if is_home else g.home_score
            if own_score > opp_score:
                res = "W"
            elif own_score < opp_score:
                res = "L"
            else:
                res = "D"
            form.append(FormResult(result=res, game_id=g.game_id))
        form.reverse()  # oldest first

        standings.append(ConferenceStanding(
            school_id=school.id,
            school_name=school.name,
            abbreviation=school.abbreviation,
            gender=school.gender or gender,
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
        ))

    # Sort: points DESC, goal_diff DESC, goals_for DESC
    standings.sort(key=lambda s: (s.points, s.goal_diff, s.goals_for), reverse=True)
    return standings
