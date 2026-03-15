"""create core schema

Revision ID: 001
Revises:
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schools",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("abbreviation", sa.String(20), nullable=False, unique=True),
        sa.Column("conference", sa.String(100)),
        sa.Column("mascot", sa.String(100)),
    )

    op.create_table(
        "games",
        sa.Column("game_id", sa.Integer, primary_key=True, autoincrement=False),
        sa.Column(
            "school_id", sa.Integer, sa.ForeignKey("schools.id"), nullable=False
        ),
        sa.Column("season_year", sa.Integer, nullable=False),
        sa.Column("source_url", sa.Text),
        sa.Column("date", sa.Date),
        sa.Column("venue", sa.String(255)),
        sa.Column("attendance", sa.Integer),
        sa.Column("home_team", sa.String(255)),
        sa.Column("away_team", sa.String(255)),
        sa.Column("home_score", sa.Integer),
        sa.Column("away_score", sa.Integer),
    )
    op.create_index(
        "idx_games_school_season", "games", ["school_id", "season_year"]
    )

    op.create_table(
        "team_game_stats",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "game_id", sa.Integer, sa.ForeignKey("games.game_id"), nullable=False
        ),
        sa.Column(
            "school_id", sa.Integer, sa.ForeignKey("schools.id"), nullable=False
        ),
        sa.Column("team", sa.String(255)),
        sa.Column("is_home", sa.Boolean),
        sa.Column("shots", sa.Integer),
        sa.Column("shots_on_goal", sa.Integer),
        sa.Column("goals", sa.Integer),
        sa.Column("corners", sa.Integer),
        sa.Column("saves", sa.Integer),
    )
    op.create_index("idx_team_game_stats_school", "team_game_stats", ["school_id"])
    op.create_index("idx_team_game_stats_game", "team_game_stats", ["game_id"])

    op.create_table(
        "player_game_stats",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "game_id", sa.Integer, sa.ForeignKey("games.game_id"), nullable=False
        ),
        sa.Column(
            "school_id", sa.Integer, sa.ForeignKey("schools.id"), nullable=False
        ),
        sa.Column("team", sa.String(255)),
        sa.Column("jersey_number", sa.String(10)),
        sa.Column("player_name", sa.String(255)),
        sa.Column("position", sa.String(50)),
        sa.Column("is_starter", sa.Boolean),
        sa.Column("minutes", sa.Integer),
        sa.Column("shots", sa.Integer),
        sa.Column("shots_on_goal", sa.Integer),
        sa.Column("goals", sa.Integer),
        sa.Column("assists", sa.Integer),
    )
    op.create_index(
        "idx_player_game_stats_school", "player_game_stats", ["school_id"]
    )
    op.create_index("idx_player_game_stats_game", "player_game_stats", ["game_id"])

    op.create_table(
        "game_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "game_id", sa.Integer, sa.ForeignKey("games.game_id"), nullable=False
        ),
        sa.Column(
            "school_id", sa.Integer, sa.ForeignKey("schools.id"), nullable=False
        ),
        sa.Column("event_type", sa.String(50)),
        sa.Column("clock", sa.String(20)),
        sa.Column("team", sa.String(255)),
        sa.Column("player", sa.String(255)),
        sa.Column("assist1", sa.String(255)),
        sa.Column("assist2", sa.String(255)),
        sa.Column("description", sa.Text),
    )
    op.create_index("idx_game_events_school", "game_events", ["school_id"])
    op.create_index("idx_game_events_game", "game_events", ["game_id"])


def downgrade() -> None:
    op.drop_table("game_events")
    op.drop_table("player_game_stats")
    op.drop_table("team_game_stats")
    op.drop_table("games")
    op.drop_table("schools")
