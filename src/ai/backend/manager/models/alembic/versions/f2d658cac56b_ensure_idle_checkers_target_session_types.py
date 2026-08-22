"""ensure idle_checkers.target_session_types exists

26.7.0 released ``d3f8a1c45e9b`` without ``target_session_types``; the column
was later added by editing that migration in place (#12398), so databases
migrated in that window never received it and the idle-check queries fail
with UndefinedColumnError. Re-adds the column idempotently (no-op where it
already exists); pre-existing rows are backfilled with an empty array so
checkers created before the column existed stay inert until an admin assigns
target types.

Revision ID: f2d658cac56b
Revises: f1a7c3e9b482
Create Date: 2026-08-12 17:30:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f2d658cac56b"
down_revision = "f1a7c3e9b482"
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
