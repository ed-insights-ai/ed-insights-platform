"""idempotently seed the 14 canonical GAC soccer programs

Revision ID: 005
Revises: 004
Create Date: 2026-03-16

Additive only per ADR-007: inserts missing schools by abbreviation and deletes nothing.
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
    # One-time forward correction (ADR-007): ensure the 14 canonical GAC
    # programs exist. Additive and idempotent so re-running is a no-op.
    for school in CORRECT_SCHOOLS:
        op.execute(
            sa.text(
                "INSERT INTO schools "
                "(name, abbreviation, conference, mascot, gender, enabled) "
                "VALUES (:name, :abbreviation, :conference, :mascot, :gender, :enabled) "
                "ON CONFLICT (abbreviation) DO NOTHING"
            ).bindparams(**school)
        )


def downgrade() -> None:
    # No-op: 005 only inserts missing schools and deletes nothing, so there
    # is nothing to reverse without risking rows this migration did not create.
    pass
