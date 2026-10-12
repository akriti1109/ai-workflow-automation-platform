"""add processing workflow request status

Revision ID: 20261004_0002
Revises: 20261004_0001
Create Date: 2026-10-04

"""
from typing import Sequence, Union

from alembic import op


revision: str = "20261004_0002"
down_revision: Union[str, None] = "20261004_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE request_status ADD VALUE IF NOT EXISTS 'processing'")


def downgrade() -> None:
    # PostgreSQL cannot safely drop enum values without recreating the type.
    pass

