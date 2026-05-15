"""Add health_check column to routings table.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-15

"""

# Part of: 26.5.0

from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b2d4f6e8c1a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("ALTER TABLE routings ADD COLUMN IF NOT EXISTS health_check JSONB")
    # Backfill health_check from revision's model_definition for existing routes.
    # Applies ModelHealthCheck defaults for optional fields (interval, max_retries, etc.).
    # Only populates when health_check.path exists (required field in ModelHealthCheck).
    conn.exec_driver_sql("""
        UPDATE routings r
        SET health_check = jsonb_build_object(
            'path',                  dr.model_definition->'health_check'->>'path',
            'interval',              COALESCE((dr.model_definition->'health_check'->>'interval')::float,    10.0),
            'max_retries',           COALESCE((dr.model_definition->'health_check'->>'max_retries')::int,   10),
            'max_wait_time',         COALESCE((dr.model_definition->'health_check'->>'max_wait_time')::float, 15.0),
            'expected_status_code',  COALESCE((dr.model_definition->'health_check'->>'expected_status_code')::int, 200),
            'initial_delay',         COALESCE((dr.model_definition->'health_check'->>'initial_delay')::float, 60.0)
        )
        FROM deployment_revisions dr
        WHERE dr.id = r.revision
          AND r.health_check IS NULL
          AND dr.model_definition IS NOT NULL
          AND dr.model_definition->'health_check' IS NOT NULL
          AND dr.model_definition->'health_check'->>'path' IS NOT NULL
    """)


def downgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql("ALTER TABLE routings DROP COLUMN IF EXISTS health_check")
