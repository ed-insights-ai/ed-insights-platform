"""add gender and enabled columns to schools

Revision ID: 004
Revises: 003
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("schools", sa.Column("gender", sa.String(10), nullable=True, server_default="men"))
    op.add_column("schools", sa.Column("enabled", sa.Boolean(), nullable=True, server_default=sa.text("true")))


def downgrade() -> None:
    op.drop_column("schools", "enabled")
    op.drop_column("schools", "gender")
