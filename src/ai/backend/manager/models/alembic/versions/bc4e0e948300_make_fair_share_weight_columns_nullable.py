"""make fair share weight columns nullable

Revision ID: bc4e0e948300
Revises: 3b27edfaae20
Create Date: 2026-01-22 16:30:09.032337

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bc4e0e948300"
down_revision = "3b27edfaae20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make weight columns nullable in fair share tables
    # When weight is NULL, the resource group's default_weight should be used
    op.alter_column(
        "domain_fair_shares",
        "weight",
        existing_type=sa.Numeric(precision=10, scale=4),
        nullable=True,
    )
    op.alter_column(
        "project_fair_shares",
        "weight",
        existing_type=sa.Numeric(precision=10, scale=4),
        nullable=True,
    )
    op.alter_column(
        "user_fair_shares",
        "weight",
        existing_type=sa.Numeric(precision=10, scale=4),
        nullable=True,
    )


def downgrade() -> None:
    # Revert weight columns to NOT NULL with default value
    # First update any NULL values to default 1.0
    op.execute("UPDATE domain_fair_shares SET weight = 1.0 WHERE weight IS NULL")
    op.execute("UPDATE project_fair_shares SET weight = 1.0 WHERE weight IS NULL")
    op.execute("UPDATE user_fair_shares SET weight = 1.0 WHERE weight IS NULL")

    op.alter_column(
        "domain_fair_shares",
        "weight",
        existing_type=sa.Numeric(precision=10, scale=4),
        nullable=False,
    )
    op.alter_column(
        "project_fair_shares",
        "weight",
        existing_type=sa.Numeric(precision=10, scale=4),
        nullable=False,
    )
    op.alter_column(
        "user_fair_shares",
        "weight",
        existing_type=sa.Numeric(precision=10, scale=4),
        nullable=False,
    )
