from datetime import date

from pydantic import BaseModel


class SchoolResponse(BaseModel):
    id: int
    name: str
    abbreviation: str
    conference: str | None = None
    mascot: str | None = None

    model_config = {"from_attributes": True}


class GameSummary(BaseModel):
    game_id: int
    school_id: int
    season_year: int
    date: date | None = None
    venue: str | None = None
    home_team: str | None = None
    away_team: str | None = None
    home_score: int | None = None
    away_score: int | None = None

    model_config = {"from_attributes": True}


class TeamGameStatsResponse(BaseModel):
    id: int
    game_id: int
    school_id: int
    team: str | None = None
    is_home: bool | None = None
    shots: int | None = None
    shots_on_goal: int | None = None
    goals: int | None = None
    corners: int | None = None
    saves: int | None = None

    model_config = {"from_attributes": True}


class PlayerGameStatsResponse(BaseModel):
    id: int
    game_id: int
    school_id: int
    team: str | None = None
    jersey_number: str | None = None
    player_name: str | None = None
    position: str | None = None
    is_starter: bool | None = None
    minutes: int | None = None
    shots: int | None = None
    shots_on_goal: int | None = None
    goals: int | None = None
    assists: int | None = None

    model_config = {"from_attributes": True}


class GameEventResponse(BaseModel):
    id: int
    game_id: int
    school_id: int
    event_type: str | None = None
    clock: str | None = None
    team: str | None = None
    player: str | None = None
    assist1: str | None = None
    assist2: str | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class GameDetail(BaseModel):
    game_id: int
    school_id: int
    season_year: int
    source_url: str | None = None
    date: date | None = None
    venue: str | None = None
    attendance: int | None = None
    home_team: str | None = None
    away_team: str | None = None
    home_score: int | None = None
    away_score: int | None = None
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
