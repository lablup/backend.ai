"""Move role soft delete to deleted_at."""

import sqlalchemy as sa
from alembic import op

revision = "b0be613bca9b"
down_revision = "fa2dfd48c169"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE roles SET deleted_at = COALESCE(deleted_at, now()), status = 'inactive' "
            "WHERE status = 'deleted'"
        )
    )
    op.alter_column("roles", "deleted_at", server_default=sa.null())


def downgrade() -> None:
    op.alter_column("roles", "deleted_at", server_default=None)
    op.execute(sa.text("UPDATE roles SET status = 'deleted' WHERE deleted_at IS NOT NULL"))
