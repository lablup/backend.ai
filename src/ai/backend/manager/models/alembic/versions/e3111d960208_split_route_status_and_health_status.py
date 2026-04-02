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

    # 2. Add health_status column to routings
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

    # 4. Add replica connection info to routings
    op.execute("""
        ALTER TABLE routings
        ADD COLUMN IF NOT EXISTS replica_host VARCHAR(256)
    """)
    op.execute("""
        ALTER TABLE routings
        ADD COLUMN IF NOT EXISTS replica_port INTEGER
    """)

    # 5. Backfill replica_host/replica_port from kernels for existing running routes
    op.execute("""
        UPDATE routings r SET
            replica_host = k.kernel_host,
            replica_port = (
                SELECT (sp->>'host_ports')::jsonb->>0
                FROM jsonb_array_elements(k.service_ports::jsonb) sp
                WHERE (sp->>'is_inference')::boolean = true
                LIMIT 1
            )::integer
        FROM kernels k
        WHERE k.session_id = r.session
          AND k.cluster_role = 'main'
          AND r.status = 'running'
          AND r.replica_host IS NULL
    """)

    # 6. Add category, from_health_status, to_health_status to route_history
    op.execute("""
        ALTER TABLE route_history
        ADD COLUMN IF NOT EXISTS category VARCHAR(32) NOT NULL DEFAULT 'lifecycle'
    """)
    op.execute("""
        ALTER TABLE route_history
        ADD COLUMN IF NOT EXISTS from_health_status VARCHAR(64)
    """)
    op.execute("""
        ALTER TABLE route_history
        ADD COLUMN IF NOT EXISTS to_health_status VARCHAR(64)
    """)


def downgrade() -> None:
    # Remove replica connection info
    op.execute("ALTER TABLE routings DROP COLUMN IF EXISTS replica_port")
    op.execute("ALTER TABLE routings DROP COLUMN IF EXISTS replica_host")

    # Remove route_history columns
    op.execute("ALTER TABLE route_history DROP COLUMN IF EXISTS to_health_status")
    op.execute("ALTER TABLE route_history DROP COLUMN IF EXISTS from_health_status")
    op.execute("ALTER TABLE route_history DROP COLUMN IF EXISTS category")

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
