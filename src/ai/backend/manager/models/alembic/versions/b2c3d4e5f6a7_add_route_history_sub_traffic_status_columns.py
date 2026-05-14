"""Add sub_status columns to route_history and drop health_status columns.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-05-14

"""

# Part of: 26.5.0

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    for col in ("from_sub_status", "to_sub_status"):
        conn.exec_driver_sql(
            f"ALTER TABLE route_history ADD COLUMN IF NOT EXISTS {col} VARCHAR(64)"
        )
    for col in ("from_health_status", "to_health_status"):
        conn.exec_driver_sql(f"ALTER TABLE route_history DROP COLUMN IF EXISTS {col}")


def downgrade() -> None:
    conn = op.get_bind()
    for col in ("to_sub_status", "from_sub_status"):
        op.drop_column("route_history", col)
    for col in ("from_health_status", "to_health_status"):
        conn.exec_driver_sql(
            f"ALTER TABLE route_history ADD COLUMN IF NOT EXISTS {col} VARCHAR(64)"
        )
