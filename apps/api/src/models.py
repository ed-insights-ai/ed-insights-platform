from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    abbreviation = Column(String(20), nullable=False, unique=True)
    conference = Column(String(100))
    mascot = Column(String(100))

    games = relationship("Game", back_populates="school")


class Game(Base):
    __tablename__ = "games"

    game_id = Column(Integer, primary_key=True, autoincrement=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    season_year = Column(Integer, nullable=False)
    source_url = Column(Text)
    date = Column(Date)
    venue = Column(String(255))
    attendance = Column(Integer)
    home_team = Column(String(255))
    away_team = Column(String(255))
    home_score = Column(Integer)
    away_score = Column(Integer)

    school = relationship("School", back_populates="games")
    team_stats = relationship("TeamGameStats", back_populates="game")
    player_stats = relationship("PlayerGameStats", back_populates="game")
    events = relationship("GameEvent", back_populates="game")

    __table_args__ = (
        Index("idx_games_school_season", "school_id", "season_year"),
    )


class TeamGameStats(Base):
    __tablename__ = "team_game_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    team = Column(String(255))
    is_home = Column(Boolean)
    shots = Column(Integer)
    shots_on_goal = Column(Integer)
    goals = Column(Integer)
    corners = Column(Integer)
    saves = Column(Integer)

    game = relationship("Game", back_populates="team_stats")
    school = relationship("School")

    __table_args__ = (
        Index("idx_team_game_stats_school", "school_id"),
        Index("idx_team_game_stats_game", "game_id"),
    )


class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    team = Column(String(255))
    jersey_number = Column(String(10))
    player_name = Column(String(255))
    position = Column(String(50))
    is_starter = Column(Boolean)
    minutes = Column(Integer)
    shots = Column(Integer)
    shots_on_goal = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)

    game = relationship("Game", back_populates="player_stats")
    school = relationship("School")

    __table_args__ = (
        Index("idx_player_game_stats_school", "school_id"),
        Index("idx_player_game_stats_game", "game_id"),
    )


class GameEvent(Base):
    __tablename__ = "game_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    event_type = Column(String(50))
    clock = Column(String(20))
    team = Column(String(255))
    player = Column(String(255))
    assist1 = Column(String(255))
    assist2 = Column(String(255))
    description = Column(Text)

    game = relationship("Game", back_populates="events")
    school = relationship("School")

    __table_args__ = (
        Index("idx_game_events_school", "school_id"),
        Index("idx_game_events_game", "game_id"),
    )
