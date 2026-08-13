"""rename domains.modified_at to updated_at

``domains`` kept a hand-rolled ``modified_at`` while the tables renamed in
``2dccb3069031`` moved onto ``LifecycleTimestampsMixin``'s ``updated_at``.
That migration also tightened the timestamps of the tables it touched but
left ``domains`` out, so a database that came up through ``bae1a7326e8a``
rather than ``create_all`` still allows NULLs the ORM declares impossible.

Revision ID: c4d1a7e58b32
Revises: b9e3a7c14f28
Create Date: 2026-08-13 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4d1a7e58b32"
down_revision = "b9e3a7c14f28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def _backfill_and_set_not_null(column: str, backfill: str) -> None:
    """Tighten ``domains.{column}``, skipping a database that already has it NOT NULL."""
    inspector = sa.inspect(op.get_bind())
    reflected = {col["name"]: col for col in inspector.get_columns("domains")}
    if not reflected[column]["nullable"]:
        return
    op.execute(sa.text(f"UPDATE domains SET {column} = {backfill} WHERE {column} IS NULL"))
    op.alter_column("domains", column, nullable=False)


def upgrade() -> None:
    op.alter_column("domains", "modified_at", new_column_name="updated_at")
    # created_at is tightened first, so a row with both timestamps NULL leaves
    # this call with now() for the updated_at backfill to read.
    _backfill_and_set_not_null("created_at", "COALESCE(updated_at, now())")
    _backfill_and_set_not_null("updated_at", "COALESCE(created_at, now())")


def downgrade() -> None:
    # The tightening is not reversed: upgrade only applies it to a database that
    # was still nullable, and loosening one that never was would undo a state it
    # arrived with.
    op.alter_column("domains", "updated_at", new_column_name="modified_at")
