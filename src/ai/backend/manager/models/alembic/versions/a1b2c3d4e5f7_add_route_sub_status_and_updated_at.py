"""Add route sub_status, updated_at columns and fix traffic_status default.

Revision ID: a1b2c3d4e5f7
Revises: d3f4a5b6c7d8
Create Date: 2026-05-14

"""

# Part of: 26.5.0

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "d3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Add sub_status column (nullable, defaults to 'pending' for new rows)
    conn.exec_driver_sql(
        "ALTER TABLE routings ADD COLUMN IF NOT EXISTS sub_status VARCHAR(64) DEFAULT 'pending'"
    )

    # Add updated_at as nullable first, backfill, then enforce NOT NULL
    conn.exec_driver_sql(
        "ALTER TABLE routings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE"
    )
    conn.exec_driver_sql("UPDATE routings SET updated_at = created_at WHERE updated_at IS NULL")
    conn.exec_driver_sql("ALTER TABLE routings ALTER COLUMN updated_at SET NOT NULL")
    conn.exec_driver_sql("ALTER TABLE routings ALTER COLUMN updated_at SET DEFAULT now()")

    # Clear sub_status for non-PROVISIONING rows — only meaningful during provisioning
    conn.exec_driver_sql("UPDATE routings SET sub_status = NULL WHERE status != 'provisioning'")

    # Backfill traffic_status based on lifecycle: RUNNING keeps ACTIVE, all others become INACTIVE
    conn.exec_driver_sql("""
        UPDATE routings
        SET traffic_status = CASE
            WHEN status = 'running' THEN 'active'
            ELSE 'inactive'
        END
    """)

    # Change server default for new inserts
    conn.exec_driver_sql("ALTER TABLE routings ALTER COLUMN traffic_status SET DEFAULT 'inactive'")


def downgrade() -> None:
    conn = op.get_bind()

    conn.exec_driver_sql("ALTER TABLE routings ALTER COLUMN traffic_status SET DEFAULT 'active'")
    conn.exec_driver_sql("UPDATE routings SET traffic_status = 'active'")
    op.drop_column("routings", "updated_at")
    op.drop_column("routings", "sub_status")
