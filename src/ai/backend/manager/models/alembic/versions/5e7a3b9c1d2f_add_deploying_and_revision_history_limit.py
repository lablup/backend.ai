"""add deploying lifecycle state and revision_history_limit column

Revision ID: 5e7a3b9c1d2f
Revises: 4c9e2f3a5b6d
Create Date: 2025-12-17

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5e7a3b9c1d2f"
down_revision = "4c9e2f3a5b6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'deploying' value to endpointlifecycle enum
    op.execute("ALTER TYPE endpointlifecycle ADD VALUE IF NOT EXISTS 'deploying'")

    # Add revision_history_limit column to endpoints table
    op.add_column(
        "endpoints",
        sa.Column(
            "revision_history_limit",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("10"),
        ),
    )


def downgrade() -> None:
    # Drop revision_history_limit column
    op.drop_column("endpoints", "revision_history_limit")
    # Note: PostgreSQL doesn't support removing enum values directly
    # The 'deploying' value will remain in the enum type
