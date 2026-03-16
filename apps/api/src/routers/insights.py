"""Smart Insights engine — rule-based narrative insights from SQL queries."""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Game, PlayerGameStats, School, TeamGameStats

router = APIRouter(prefix="/api", tags=["insights"])


class Insight(BaseModel):
    type: str
    priority: int
    icon: str
    text: str


class InsightsResponse(BaseModel):
    insights: list[Insight]


# --------------- helpers ---------------


async def _resolve_school(
    db: AsyncSession, abbr: str
) -> tuple[int, str] | None:
    """Return (school_id, school_name) or None."""
    row = (
        await db.execute(
            select(School.id, School.name).where(School.abbreviation == abbr)
        )
    ).first()
    return (row[0], row[1]) if row else None


async def _completed_games(
    db: AsyncSession, school_id: int, season: int
) -> list[Game]:
    """Return completed games ordered by date descending."""
    result = await db.execute(
        select(Game)
        .where(
            Game.school_id == school_id,
            Game.season_year == season,
            Game.home_score.is_not(None),
        )
        .order_by(Game.date.desc())
    )
    return list(result.scalars().all())


def _game_result(game: Game, school_name: str) -> str:
    """Return 'W', 'L', or 'D' for a completed game."""
    is_home = (game.home_team or "").lower().find(school_name.lower()) >= 0
    gf = game.home_score if is_home else game.away_score
    ga = game.away_score if is_home else game.home_score
    if gf > ga:
        return "W"
    if gf < ga:
        return "L"
    return "D"


def _goals_for(game: Game, school_name: str) -> int:
    is_home = (game.home_team or "").lower().find(school_name.lower()) >= 0
    return game.home_score if is_home else game.away_score


def _goals_against(game: Game, school_name: str) -> int:
    is_home = (game.home_team or "").lower().find(school_name.lower()) >= 0
    return game.away_score if is_home else game.home_score


def _is_home(game: Game, school_name: str) -> bool:
    return (game.home_team or "").lower().find(school_name.lower()) >= 0


# --------------- insight rules ---------------


async def _scoring_streak(
    db: AsyncSession, school_id: int, season: int, school_name: str
) -> Optional[Insight]:
    """Rule 1: Player with longest current scoring streak >= 3 games."""
    # Get all players with goals in recent games
    result = await db.execute(
        select(
            PlayerGameStats.player_name,
            Game.date,
            PlayerGameStats.goals,
        )
        .join(Game, Game.game_id == PlayerGameStats.game_id)
        .where(
            PlayerGameStats.school_id == school_id,
            Game.season_year == season,
            Game.home_score.is_not(None),
            # Only count the school's own players
            func.lower(PlayerGameStats.team).contains(school_name.lower()),
        )
        .order_by(Game.date.desc())
    )
    rows = result.all()

    # Group by player, check consecutive streak from most recent
    player_games: dict[str, list[int]] = {}
    for name, _date, goals in rows:
        if name not in player_games:
            player_games[name] = []
        player_games[name].append(goals or 0)

    best_player = None
    best_streak = 0
    for player, goal_list in player_games.items():
        streak = 0
        for g in goal_list:  # already sorted desc by date
            if g > 0:
                streak += 1
            else:
                break
        if streak >= 3 and streak > best_streak:
            best_streak = streak
            best_player = player

    if best_player:
        return Insight(
            type="scoring_streak",
            priority=1,
            icon="🔥",
            text=f"{best_player} has scored in {best_streak} consecutive games.",
        )
    return None


async def _conversion_trend(
    db: AsyncSession, school_id: int, season: int, school_name: str
) -> Optional[Insight]:
    """Rule 2: Shot conversion in last 5 games vs season average."""
    result = await db.execute(
        select(TeamGameStats.goals, TeamGameStats.shots, Game.date)
        .join(Game, Game.game_id == TeamGameStats.game_id)
        .where(
            TeamGameStats.school_id == school_id,
            Game.season_year == season,
            Game.home_score.is_not(None),
            func.lower(TeamGameStats.team).contains(school_name.lower()),
        )
        .order_by(Game.date.desc())
    )
    rows = result.all()
    if len(rows) < 5:
        return None

    season_goals = sum(r[0] or 0 for r in rows)
    season_shots = sum(r[1] or 0 for r in rows)
    if season_shots == 0:
        return None
    season_pct = (season_goals / season_shots) * 100

    last5 = rows[:5]
    l5_goals = sum(r[0] or 0 for r in last5)
    l5_shots = sum(r[1] or 0 for r in last5)
    if l5_shots == 0:
        return None
    l5_pct = (l5_goals / l5_shots) * 100

    diff = l5_pct - season_pct
    if abs(diff) < 3:
        return None

    if diff < 0:
        text = (
            f"Shot conversion has dropped {abs(diff):.1f}% over the last 5 games "
            f"({l5_pct:.1f}% vs {season_pct:.1f}% season avg)."
        )
    else:
        text = (
            f"Shot conversion is up {diff:.1f}% over the last 5 games "
            f"({l5_pct:.1f}% vs {season_pct:.1f}% season avg)."
        )

    return Insight(
        type="conversion_trend",
        priority=2,
        icon="📈" if diff > 0 else "📉",
        text=text,
    )


async def _unbeaten_run(
    db: AsyncSession, school_id: int, season: int, school_name: str
) -> Optional[Insight]:
    """Rule 3: Unbeaten in last N>=4 games."""
    games = await _completed_games(db, school_id, season)
    if len(games) < 4:
        return None

    streak = 0
    wins = 0
    draws = 0
    for g in games:
        r = _game_result(g, school_name)
        if r == "L":
            break
        streak += 1
        if r == "W":
            wins += 1
        else:
            draws += 1

    if streak < 4:
        return None

    record = f"{wins}W {draws}D"
    return Insight(
        type="unbeaten_run",
        priority=1,
        icon="🏆",
        text=f"{school_name} is unbeaten in their last {streak} games ({record}).",
    )


async def _losing_streak(
    db: AsyncSession, school_id: int, season: int, school_name: str
) -> Optional[Insight]:
    """Rule 4: Lost N>=3 consecutive games."""
    games = await _completed_games(db, school_id, season)
    if len(games) < 3:
        return None

    streak = 0
    for g in games:
        if _game_result(g, school_name) == "L":
            streak += 1
        else:
            break

    if streak < 3:
        return None

    return Insight(
        type="losing_streak",
        priority=1,
        icon="📉",
        text=f"{school_name} has lost {streak} consecutive games.",
    )


async def _clean_sheet_split(
    db: AsyncSession, school_id: int, season: int, school_name: str
) -> Optional[Insight]:
    """Rule 5: Clean sheet home/away disparity."""
    games = await _completed_games(db, school_id, season)

    home_cs = 0
    away_cs = 0
    for g in games:
        ga = _goals_against(g, school_name)
        if ga == 0:
            if _is_home(g, school_name):
                home_cs += 1
            else:
                away_cs += 1

    if home_cs == away_cs:
        return None
    if not ((home_cs == 0 and away_cs >= 3) or (away_cs == 0 and home_cs >= 3)):
        return None

    return Insight(
        type="clean_sheet_split",
        priority=3,
        icon="🏠",
        text=(
            f"{school_name} has kept {home_cs} clean sheet(s) at home "
            f"but {away_cs} on the road."
        ),
    )


async def _top_scorer_pace(
    db: AsyncSession, school_id: int, season: int, school_name: str
) -> Optional[Insight]:
    """Rule 6: Top scorer with goals_per_game >= 0.6."""
    result = await db.execute(
        select(
            PlayerGameStats.player_name,
            func.sum(PlayerGameStats.goals).label("total_goals"),
            func.count(PlayerGameStats.id).label("games_played"),
        )
        .join(Game, Game.game_id == PlayerGameStats.game_id)
        .where(
            PlayerGameStats.school_id == school_id,
            Game.season_year == season,
            Game.home_score.is_not(None),
            func.lower(PlayerGameStats.team).contains(school_name.lower()),
        )
        .group_by(PlayerGameStats.player_name)
        .order_by(func.sum(PlayerGameStats.goals).desc())
        .limit(1)
    )
    row = result.first()
    if not row:
        return None

    name, total_goals, gp = row
    if gp == 0 or total_goals == 0:
        return None
    gpg = total_goals / gp
    if gpg < 0.6:
        return None

    return Insight(
        type="top_scorer_pace",
        priority=2,
        icon="⚽",
        text=(
            f"{name} is scoring at {gpg:.2f} goals per game "
            f"— {total_goals} goals in {gp} appearances."
        ),
    )


async def _conf_split(
    db: AsyncSession, school_id: int, season: int, school_name: str
) -> Optional[Insight]:
    """Rule 7: Conference vs non-conference win rate difference >= 25%."""
    games = await _completed_games(db, school_id, season)

    conf = {"w": 0, "l": 0, "d": 0}
    nonconf = {"w": 0, "l": 0, "d": 0}

    for g in games:
        bucket = conf if g.is_conference_game else nonconf
        r = _game_result(g, school_name)
        if r == "W":
            bucket["w"] += 1
        elif r == "L":
            bucket["l"] += 1
        else:
            bucket["d"] += 1

    conf_total = conf["w"] + conf["l"] + conf["d"]
    nonconf_total = nonconf["w"] + nonconf["l"] + nonconf["d"]
    if conf_total == 0 or nonconf_total == 0:
        return None

    conf_wr = conf["w"] / conf_total * 100
    nonconf_wr = nonconf["w"] / nonconf_total * 100
    diff = conf_wr - nonconf_wr

    if abs(diff) < 25:
        return None

    def fmt(b: dict) -> str:
        return f"{b['w']}W-{b['l']}L-{b['d']}D"

    if diff > 0:
        text = (
            f"{school_name} performs significantly better in conference play "
            f"({fmt(conf)} conf vs {fmt(nonconf)} non-conf)."
        )
    else:
        text = (
            f"{school_name} is struggling in conference play "
            f"({fmt(conf)} conf vs {fmt(nonconf)} non-conf)."
        )

    return Insight(
        type="conf_split",
        priority=3,
        icon="🏟️",
        text=text,
    )


async def _goal_drought(
    db: AsyncSession, school_id: int, season: int, school_name: str
) -> Optional[Insight]:
    """Rule 8: Failed to score in N>=3 consecutive games."""
    games = await _completed_games(db, school_id, season)
    if len(games) < 3:
        return None

    streak = 0
    for g in games:
        if _goals_for(g, school_name) == 0:
            streak += 1
        else:
            break

    if streak < 3:
        return None

    return Insight(
        type="goal_drought",
        priority=1,
        icon="🚫",
        text=f"{school_name} has failed to score in {streak} consecutive games.",
    )


# --------------- endpoint ---------------

STREAK_TYPES = {"scoring_streak", "unbeaten_run", "losing_streak", "goal_drought"}


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(
    school: str = Query(...),
    season: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    info = await _resolve_school(db, school)
    if not info:
        return InsightsResponse(insights=[])

    school_id, school_name = info

    results = await asyncio.gather(
        _scoring_streak(db, school_id, season, school_name),
        _conversion_trend(db, school_id, season, school_name),
        _unbeaten_run(db, school_id, season, school_name),
        _losing_streak(db, school_id, season, school_name),
        _clean_sheet_split(db, school_id, season, school_name),
        _top_scorer_pace(db, school_id, season, school_name),
        _conf_split(db, school_id, season, school_name),
        _goal_drought(db, school_id, season, school_name),
    )

    insights = [r for r in results if r is not None]

    # Sort by priority (lower first)
    insights.sort(key=lambda i: i.priority)

    # Deduplicate streak insights: keep only the most dramatic one
    streak_insights = [i for i in insights if i.type in STREAK_TYPES]
    non_streak = [i for i in insights if i.type not in STREAK_TYPES]

    # Never return both unbeaten_run and losing_streak
    if streak_insights:
        kept = streak_insights[0]  # already sorted by priority, first is best
        insights = [kept] + non_streak
        insights.sort(key=lambda i: i.priority)

    return InsightsResponse(insights=insights[:4])
