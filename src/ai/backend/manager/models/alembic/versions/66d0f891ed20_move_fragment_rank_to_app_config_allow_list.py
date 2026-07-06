"""move fragment rank to app_config_allow_list

Move the merge-priority ``rank`` from ``app_config_fragments`` to
``app_config_allow_list`` (BEP-1052). Fragment writes are partly user-owned, so
a rank on the fragment would let a fragment owner re-order the merge; the
allow-list entry is admin-owned, making it the right carrier for merge
priority. Existing allow-list rows are backfilled with a fixed default rank
(per-scope-type defaults follow in a later revision).

Revision ID: 66d0f891ed20
Revises: a379b72f1206
Create Date: 2026-07-03

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "66d0f891ed20"
down_revision = "a379b72f1206"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Allow-list entries carry the merge rank; backfill existing rows with the default.
    op.add_column("app_config_allow_list", sa.Column("rank", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE app_config_allow_list
            SET rank = 100
            WHERE rank IS NULL
            """
        )
    )
    op.alter_column("app_config_allow_list", "rank", nullable=False)
    op.drop_column("app_config_fragments", "rank")


def downgrade() -> None:
    op.add_column("app_config_fragments", sa.Column("rank", sa.Integer(), nullable=True))
    # Restore each fragment's rank from its allow-list entry. Fragments whose entry
    # was removed fall back to the default rank; fragments sharing a
    # ``(config_name, scope_type)`` end up with equal ranks — the pre-move
    # per-fragment next-value ranks are not recoverable.
    op.execute(
        sa.text(
            """
            UPDATE app_config_fragments f
            SET rank = al.rank
            FROM app_config_allow_list al
            WHERE al.config_name = f.config_name
              AND al.scope_type = f.scope_type
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE app_config_fragments
            SET rank = 100
            WHERE rank IS NULL
            """
        )
    )
    op.alter_column("app_config_fragments", "rank", nullable=False)
    op.drop_column("app_config_allow_list", "rank")
