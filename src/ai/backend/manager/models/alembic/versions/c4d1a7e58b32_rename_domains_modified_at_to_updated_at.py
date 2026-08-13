"""rename domains.modified_at to updated_at

``domains`` kept a hand-rolled ``modified_at`` while the tables renamed in
``2dccb3069031`` moved onto ``LifecycleTimestampsMixin``'s ``updated_at``.

Revision ID: c4d1a7e58b32
Revises: b9e3a7c14f28
Create Date: 2026-08-13 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c4d1a7e58b32"
down_revision = "b9e3a7c14f28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("domains", "modified_at", new_column_name="updated_at")


def downgrade() -> None:
    op.alter_column("domains", "updated_at", new_column_name="modified_at")
