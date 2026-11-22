"""Add the admission mode and the member count to session_groups (BEP-1083).

Existing groups become `independent` with no member count, which keeps their behavior.

Revision ID: dc09f3d488de
Revises: c26a61030407
Create Date: 2026-11-22

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "dc09f3d488de"
down_revision = "c26a61030407"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

MEMBER_COUNT_CHECK = "ck_session_groups_member_count"

ADD_COLUMNS_SQL = (
    "ALTER TABLE session_groups"
    " ADD COLUMN IF NOT EXISTS admission VARCHAR(64) NOT NULL DEFAULT 'independent'",
    "ALTER TABLE session_groups ADD COLUMN IF NOT EXISTS member_count INTEGER",
)

ADD_CHECK_SQL = f"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = '{MEMBER_COUNT_CHECK}'
          AND conrelid = 'session_groups'::regclass
    ) THEN
        ALTER TABLE session_groups ADD CONSTRAINT {MEMBER_COUNT_CHECK} CHECK (
            (admission = 'independent' AND member_count IS NULL)
            OR (admission = 'all_or_none' AND member_count IS NOT NULL AND member_count >= 2)
        );
    END IF;
END
$$;
"""


def add_admission_columns(conn: Connection) -> None:
    """Add both columns and their check; a column or check already there is left alone."""
    for statement in ADD_COLUMNS_SQL:
        conn.execute(sa.text(statement))
    conn.execute(sa.text(ADD_CHECK_SQL))


def drop_admission_columns(conn: Connection) -> None:
    conn.execute(
        sa.text(f"ALTER TABLE session_groups DROP CONSTRAINT IF EXISTS {MEMBER_COUNT_CHECK}")
    )
    conn.execute(sa.text("ALTER TABLE session_groups DROP COLUMN IF EXISTS member_count"))
    conn.execute(sa.text("ALTER TABLE session_groups DROP COLUMN IF EXISTS admission"))


def upgrade() -> None:
    add_admission_columns(op.get_bind())


def downgrade() -> None:
    drop_admission_columns(op.get_bind())
