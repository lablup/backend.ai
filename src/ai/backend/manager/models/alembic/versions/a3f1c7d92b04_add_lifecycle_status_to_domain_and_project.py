"""Add the lifecycle status column to domain and project, and the purge statuses to user and image

Revision ID: a3f1c7d92b04
Revises: a3d17c9b45e2
Create Date: 2026-08-24 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3f1c7d92b04"
down_revision = "a3d17c9b45e2"
branch_labels = None
depends_on = None

STATUS_TABLES = ("domains", "groups")


def upgrade() -> None:
    for table in STATUS_TABLES:
        op.add_column(
            table,
            sa.Column("status", sa.String(length=64), nullable=False, server_default="active"),
        )
        op.create_index(f"ix_{table}_status", table, ["status"])
        op.execute(sa.text(f"UPDATE {table} SET status = 'deleted' WHERE is_active IS FALSE"))
    op.execute(sa.text("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'purging'"))
    op.execute(sa.text("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'purge-error'"))


def downgrade() -> None:
    # The 'purging' and 'purge-error' labels stay on the userstatus enum type.
    # PostgreSQL cannot drop enum labels.
    op.execute(
        sa.text("UPDATE users SET status = 'deleted' WHERE status IN ('purging', 'purge-error')")
    )
    for table in STATUS_TABLES:
        op.drop_index(f"ix_{table}_status", table)
        op.drop_column(table, "status")
