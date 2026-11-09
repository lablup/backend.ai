"""mark dangling personal projects deleted

A personal project outlives its creator with a NULL ``creator_id``. The retention
sweep now collects only those marked ``deleted``, so rows left dangling before this
migration would never be collected. Mark them deleted at upgrade time; the retention
period starts from here.

Revision ID: a9c4e2f71b63
Revises: ece8800e945c
Create Date: 2026-11-05 06:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a9c4e2f71b63"
down_revision = "ece8800e945c"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_MARK_DANGLING_DELETED = sa.text("""
    UPDATE groups
    SET status = 'deleted', is_active = false, updated_at = now()
    WHERE type = 'personal' AND creator_id IS NULL
""")


def upgrade() -> None:
    backfill(op.get_bind())


def backfill(conn: sa.Connection) -> None:
    """Mark every dangling personal project deleted. Takes its connection so a test
    can run it against a real database — static analysis does not reach SQL."""
    conn.execute(_MARK_DANGLING_DELETED)


def downgrade() -> None:
    # The status records that the project's creator is gone; that stays true after a
    # downgrade, so there is nothing to restore.
    pass
