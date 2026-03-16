"""add conference fields and opponents table

Revision ID: 003
Revises: 002
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("is_conference_game", sa.Boolean(), nullable=True))
    op.add_column("games", sa.Column("home_conference", sa.String(100), nullable=True))
    op.add_column("games", sa.Column("away_conference", sa.String(100), nullable=True))

    op.create_table(
        "opponents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("abbreviation", sa.String(20), nullable=True),
        sa.Column("conference", sa.String(100), nullable=True),
        sa.Column("division", sa.String(10), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("opponents")
    op.drop_column("games", "away_conference")
    op.drop_column("games", "home_conference")
    op.drop_column("games", "is_conference_game")
