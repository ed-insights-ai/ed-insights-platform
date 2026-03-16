"""Data model dataclasses for the soccer pipeline."""

from dataclasses import dataclass


@dataclass
class GameURL:
    """A discovered game URL."""

    year: int
    game_num: int
    url: str


@dataclass
class Game:
    """Core game metadata — one row per game."""

    game_id: int
    season_year: int
    source_url: str
    date: str
    venue: str | None
    attendance: int | None
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    is_conference_game: bool | None = None
    home_conference: str | None = None
    away_conference: str | None = None


@dataclass
class TeamGameStats:
    """Aggregate team stats for a single game — two rows per game (home/away)."""

    game_id: int
    season_year: int
    team: str
    is_home: bool
    shots: int = 0
    shots_on_goal: int = 0
    goals: int = 0
    corners: int = 0
    saves: int = 0


@dataclass
class PlayerGameStats:
    """Individual player stats for a single game."""

    game_id: int
    season_year: int
    team: str
    jersey_number: int
    player_name: str
    position: str
    is_starter: bool
    minutes: int = 0
    shots: int = 0
    shots_on_goal: int = 0
    goals: int = 0
    assists: int = 0


@dataclass
class GameEvent:
    """Events during the game (goals, cards, subs, etc.)."""

    game_id: int
    season_year: int
    event_type: str  # 'goal', 'yellow_card', 'red_card', 'substitution'
    clock: str  # 'mm:ss' format
    team: str
    player: str
    assist1: str | None = None
    assist2: str | None = None
    description: str | None = None


@dataclass
class ParsedGame:
    """Container for all parsed data from a single game."""

    game: Game
    player_stats: list[PlayerGameStats]
    events: list[GameEvent]
    team_stats: list[TeamGameStats]
    abbrev_map: dict
