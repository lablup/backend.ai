"""Increase tag column length for JSON storage

Revision ID: e1a2b3c4d5f6
Revises: 352143f82276
Create Date: 2026-01-21 19:50:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5f6"
down_revision: str | None = "352143f82276"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Increase tag column length from 64 to 2048 characters to store JSON."""
    # Increase sessions.tag column length
    op.alter_column(
        "sessions",
        "tag",
        type_=sa.String(length=2048),
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )

    # Increase endpoints.tag column length
    op.alter_column(
        "endpoints",
        "tag",
        type_=sa.String(length=2048),
        existing_type=sa.String(length=64),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Revert tag column length back to 64 characters."""
    # Revert sessions.tag column length
    op.alter_column(
        "sessions",
        "tag",
        type_=sa.String(length=64),
        existing_type=sa.String(length=2048),
        existing_nullable=True,
    )

    # Revert endpoints.tag column length
    op.alter_column(
        "endpoints",
        "tag",
        type_=sa.String(length=64),
        existing_type=sa.String(length=2048),
        existing_nullable=True,
    )
