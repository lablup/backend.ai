"""Keep system_session_environ.key unique among the rows not soft-deleted

A soft-deleted row no longer holds its key, so another row at the same scope can take it.

Revision ID: 525c7d49d5e9
Revises: 91d276b3c15a
Create Date: 2026-10-27

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "525c7d49d5e9"  # Part of: NEXT_RELEASE_VERSION
down_revision = "91d276b3c15a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE system_session_environ DROP CONSTRAINT IF EXISTS uq_system_session_environ_key"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_system_session_environ_live_key "
        "ON system_session_environ (key, scope_type, scope_id) "
        "WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_system_session_environ_live_key")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_system_session_environ_key'
            ) THEN
                ALTER TABLE system_session_environ
                ADD CONSTRAINT uq_system_session_environ_key UNIQUE (key, scope_type, scope_id);
            END IF;
        END
        $$;
    """)
