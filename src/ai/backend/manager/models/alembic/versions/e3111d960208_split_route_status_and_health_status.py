"""split route status and health_status columns

Revision ID: e3111d960208
Revises: 8d01fe40664a
Create Date: 2026-04-01

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e3111d960208"
down_revision = "8d01fe40664a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add 'running' to the routestatus enum
    op.execute("ALTER TYPE routestatus ADD VALUE IF NOT EXISTS 'running'")
    # Commit so the new enum value is visible in the same transaction
    op.execute("COMMIT")

    # 2. Add health_status column (plain VARCHAR, not native enum)
    op.execute("""
        ALTER TABLE routings
        ADD COLUMN IF NOT EXISTS health_status VARCHAR(64)
        NOT NULL DEFAULT 'not_checked'
    """)

    # 3. Migrate existing status values:
    # HEALTHY/UNHEALTHY/DEGRADED → status=running + health_status=<value>
    # Other statuses → keep as-is + health_status=not_checked
    op.execute("""
        UPDATE routings SET
            health_status = CASE status::text
                WHEN 'healthy' THEN 'healthy'
                WHEN 'unhealthy' THEN 'unhealthy'
                WHEN 'degraded' THEN 'degraded'
                ELSE 'not_checked'
            END,
            status = CASE status::text
                WHEN 'healthy' THEN 'running'::routestatus
                WHEN 'unhealthy' THEN 'running'::routestatus
                WHEN 'degraded' THEN 'running'::routestatus
                ELSE status
            END
    """)


def downgrade() -> None:
    # Merge health_status back into status
    op.execute("""
        UPDATE routings SET
            status = CASE
                WHEN status::text = 'running' AND health_status = 'healthy' THEN 'healthy'::routestatus
                WHEN status::text = 'running' AND health_status = 'unhealthy' THEN 'unhealthy'::routestatus
                WHEN status::text = 'running' AND health_status = 'degraded' THEN 'degraded'::routestatus
                WHEN status::text = 'running' THEN 'degraded'::routestatus
                ELSE status
            END
    """)

    op.execute("ALTER TABLE routings DROP COLUMN IF EXISTS health_status")

    # Note: PostgreSQL does not support DROP VALUE from enum types.
    # The 'running' value remains in routestatus but won't be used after downgrade.
