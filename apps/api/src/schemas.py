from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel


class SchoolResponse(BaseModel):
    id: int
    name: str
    abbreviation: str
    conference: Optional[str] = None
    mascot: Optional[str] = None
    gender: Optional[str] = None
    enabled: Optional[bool] = True

    model_config = {"from_attributes": True}


class GameSummary(BaseModel):
    game_id: int
    school_id: int
    season_year: int
    date: Optional[datetime.date] = None
    venue: Optional[str] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    model_config = {"from_attributes": True}


class TeamGameStatsResponse(BaseModel):
    id: int
    game_id: int
    school_id: int
    team: Optional[str] = None
    is_home: Optional[bool] = None
    shots: Optional[int] = None
    shots_on_goal: Optional[int] = None
    goals: Optional[int] = None
    corners: Optional[int] = None
    saves: Optional[int] = None

    model_config = {"from_attributes": True}


class PlayerGameStatsResponse(BaseModel):
    id: int
    game_id: int
    school_id: int
    team: Optional[str] = None
    jersey_number: Optional[str] = None
    player_name: Optional[str] = None
    position: Optional[str] = None
    is_starter: Optional[bool] = None
    minutes: Optional[int] = None
    shots: Optional[int] = None
    shots_on_goal: Optional[int] = None
    goals: Optional[int] = None
    assists: Optional[int] = None

    model_config = {"from_attributes": True}


class GameEventResponse(BaseModel):
    id: int
    game_id: int
    school_id: int
    event_type: Optional[str] = None
    clock: Optional[str] = None
    team: Optional[str] = None
    player: Optional[str] = None
    assist1: Optional[str] = None
    assist2: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class GameDetail(BaseModel):
    game_id: int
    school_id: int
    season_year: int
    source_url: Optional[str] = None
    date: Optional[datetime.date] = None
    venue: Optional[str] = None
    attendance: Optional[int] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    team_stats: list[TeamGameStatsResponse] = []
    player_stats: list[PlayerGameStatsResponse] = []
    events: list[GameEventResponse] = []

    model_config = {"from_attributes": True}


class TeamStatsAggregation(BaseModel):
    school_id: int
    school_name: str
    season_year: int
    games_played: int
    total_goals: int
    total_shots: int
    total_shots_on_goal: int
    total_corners: int
    total_saves: int


class PlayerLeaderboard(BaseModel):
    player_name: str
    school_id: int
    school_name: str
    games_played: int
    total_goals: int
    total_assists: int
    total_shots: int
    total_shots_on_goal: int
    total_minutes: int


class PaginatedGames(BaseModel):
    items: list[GameSummary]
    total: int
    limit: int
    offset: int


class PaginatedPlayers(BaseModel):
    items: list[PlayerLeaderboard]
    total: int
    limit: int
    offset: int


class FormResult(BaseModel):
    result: str  # "W", "L", or "D"
    game_id: int


class ConferenceAverages(BaseModel):
    conference: str
    gender: str
    season: int
    schools_count: int
    avg_goals_per_game: float
    avg_shot_conversion: float
    avg_clean_sheet_pct: float
    avg_shots_per_game: float
    avg_sog_per_game: float


class ConferenceStanding(BaseModel):
    school_id: int
    school_name: str
    abbreviation: str
    gender: str
    games_played: int
    wins: int
    losses: int
    draws: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    ppg: float
    form: list[FormResult]  # last 5, oldest first
