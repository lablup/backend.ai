"""Replace system_session_environ.enabled with a soft delete

A disabled row goes away, and deleted_at says whether a row is soft-deleted.

Revision ID: 91d276b3c15a
Revises: f73d1b0ee986
Create Date: 2026-10-26

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "91d276b3c15a"  # Part of: NEXT_RELEASE_VERSION
down_revision = "f73d1b0ee986"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'system_session_environ' AND column_name = 'enabled'
            ) THEN
                DELETE FROM system_session_environ WHERE NOT enabled;
            END IF;
        END
        $$;
    """)
    op.execute("ALTER TABLE system_session_environ DROP COLUMN IF EXISTS enabled")
    op.execute(
        "ALTER TABLE system_session_environ "
        "ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NULL"
    )


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'system_session_environ' AND column_name = 'deleted_at'
            ) THEN
                DELETE FROM system_session_environ WHERE deleted_at IS NOT NULL;
            END IF;
        END
        $$;
    """)
    op.execute("ALTER TABLE system_session_environ DROP COLUMN IF EXISTS deleted_at")
    op.execute(
        "ALTER TABLE system_session_environ "
        "ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT true"
    )
