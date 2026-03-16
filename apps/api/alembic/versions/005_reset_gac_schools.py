"""reset schools table with correct 14 GAC programs

Revision ID: 005
Revises: 004
Create Date: 2026-03-16

Deletes all child data (game_events, player_game_stats, team_game_stats, games)
and all schools, then re-seeds with the correct 14 GAC soccer programs per ADR-007.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schools_table = sa.table(
    "schools",
    sa.column("name", sa.String),
    sa.column("abbreviation", sa.String),
    sa.column("conference", sa.String),
    sa.column("mascot", sa.String),
    sa.column("gender", sa.String),
    sa.column("enabled", sa.Boolean),
)

CORRECT_SCHOOLS = [
    # Men's (7)
    {"name": "Harding", "abbreviation": "HU", "conference": "GAC", "mascot": "Bisons", "gender": "men", "enabled": True},
    {"name": "Fort Hays State", "abbreviation": "FHSU", "conference": "GAC", "mascot": "Tigers", "gender": "men", "enabled": True},
    {"name": "Newman", "abbreviation": "NU", "conference": "GAC", "mascot": "Jets", "gender": "men", "enabled": True},
    {"name": "Northeastern State", "abbreviation": "NSU", "conference": "GAC", "mascot": "RiverHawks", "gender": "men", "enabled": False},
    {"name": "Ouachita Baptist", "abbreviation": "OBU", "conference": "GAC", "mascot": "Tigers", "gender": "men", "enabled": True},
    {"name": "Rogers State", "abbreviation": "RSU", "conference": "GAC", "mascot": "Hillcats", "gender": "men", "enabled": True},
    {"name": "Southern Nazarene", "abbreviation": "SNU", "conference": "GAC", "mascot": "Crimson Storm", "gender": "men", "enabled": True},
    # Women's (7)
    {"name": "Harding", "abbreviation": "HUW", "conference": "GAC", "mascot": "Lady Bisons", "gender": "women", "enabled": True},
    {"name": "East Central", "abbreviation": "ECU", "conference": "GAC", "mascot": "Tigers", "gender": "women", "enabled": True},
    {"name": "Northwestern Oklahoma State", "abbreviation": "NWOSU", "conference": "GAC", "mascot": "Rangers", "gender": "women", "enabled": True},
    {"name": "Oklahoma Baptist", "abbreviation": "OKBU", "conference": "GAC", "mascot": "Bison", "gender": "women", "enabled": True},
    {"name": "Ouachita Baptist", "abbreviation": "OBUW", "conference": "GAC", "mascot": "Tigers", "gender": "women", "enabled": True},
    {"name": "Southern Nazarene", "abbreviation": "SNUW", "conference": "GAC", "mascot": "Crimson Storm", "gender": "women", "enabled": True},
    {"name": "Southwestern Oklahoma State", "abbreviation": "SWOSU", "conference": "GAC", "mascot": "Bulldogs", "gender": "women", "enabled": True},
]


def upgrade() -> None:
    # Delete all child data first (order matters for FK constraints)
    op.execute(sa.text("DELETE FROM game_events"))
    op.execute(sa.text("DELETE FROM player_game_stats"))
    op.execute(sa.text("DELETE FROM team_game_stats"))
    op.execute(sa.text("DELETE FROM games"))
    op.execute(sa.text("DELETE FROM schools"))

    # Re-seed with correct 14 schools
    op.execute(schools_table.insert().values(CORRECT_SCHOOLS))


def downgrade() -> None:
    # Downgrade just clears everything — previous migrations will re-seed
    op.execute(sa.text("DELETE FROM game_events"))
    op.execute(sa.text("DELETE FROM player_game_stats"))
    op.execute(sa.text("DELETE FROM team_game_stats"))
    op.execute(sa.text("DELETE FROM games"))
    op.execute(sa.text("DELETE FROM schools"))
