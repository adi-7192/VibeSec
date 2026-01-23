"""Add cancelled status to scanstatus enum

Revision ID: 002
Revises: 001
Create Date: 2026-01-23

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'cancelled' value to scanstatus enum
    op.execute("ALTER TYPE scanstatus ADD VALUE IF NOT EXISTS 'cancelled'")
    
    # Add layman_explanation column to findings table
    op.execute("ALTER TABLE findings ADD COLUMN IF NOT EXISTS layman_explanation TEXT")


def downgrade() -> None:
    # Remove layman_explanation column
    op.execute("ALTER TABLE findings DROP COLUMN IF EXISTS layman_explanation")
    
    # Note: PostgreSQL doesn't support removing enum values directly
    # You would need to recreate the enum type if you want to remove 'cancelled'
    pass
