"""ensure idle_checkers.target_session_types exists (duplicate)

Duplicate of ``f2d658cac56b`` for databases tracking main that migrated while
``d3f8a1c45e9b`` still lacked ``target_session_types`` (between #12346 and
#12398). No-op where the column already exists.

Revision ID: 8dc37d4bbf38
Revises: c8d51e7a3b62
Create Date: 2026-08-12 17:30:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8dc37d4bbf38"
down_revision = "c8d51e7a3b62"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE idle_checkers "
        "ADD COLUMN IF NOT EXISTS target_session_types varchar(64)[] NOT NULL DEFAULT '{}'"
    )
    op.execute("ALTER TABLE idle_checkers ALTER COLUMN target_session_types DROP DEFAULT")


def downgrade() -> None:
    # The column is dropped together with the table in d3f8a1c45e9b.
    pass
