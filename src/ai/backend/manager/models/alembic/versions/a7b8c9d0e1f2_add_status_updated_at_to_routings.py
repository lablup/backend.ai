"""add status_updated_at to routings

Revision ID: a7b8c9d0e1f2
Revises: 32ad43817452
Create Date: 2026-03-02

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "32ad43817452"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "routings",
        sa.Column(
            "status_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    # Backfill existing rows with created_at value
    op.execute("UPDATE routings SET status_updated_at = COALESCE(created_at, now())")


def downgrade() -> None:
    op.drop_column("routings", "status_updated_at")
