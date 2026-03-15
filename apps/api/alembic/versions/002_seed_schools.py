"""seed school data

Revision ID: 002
Revises: 001
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schools_table = sa.table(
    "schools",
    sa.column("name", sa.String),
    sa.column("abbreviation", sa.String),
    sa.column("conference", sa.String),
    sa.column("mascot", sa.String),
)


def upgrade() -> None:
    op.execute(
        schools_table.insert().values(
            [
                {
                    "name": "Harding University",
                    "abbreviation": "HU",
                    "conference": "GAC",
                    "mascot": "Bisons",
                },
                {
                    "name": "Harding University (Women)",
                    "abbreviation": "HUW",
                    "conference": "GAC",
                    "mascot": "Lady Bisons",
                },
            ]
        )
    )


def downgrade() -> None:
    op.execute(
        schools_table.delete().where(
            schools_table.c.abbreviation.in_(["HU", "HUW"])
        )
    )
