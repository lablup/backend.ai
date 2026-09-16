"""drop vfolder_permissions

The per-user mount level lives in ``vfolder_user_mount_policies`` and access in the
share graph, both filled from this table earlier in the chain. Nothing reads or writes
it any more.

Revision ID: f6c9e4a2b730
Revises: e5b8d3f0a129
Create Date: 2026-09-16

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "f6c9e4a2b730"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e5b8d3f0a129"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("vfolder_permissions")


def downgrade() -> None:
    # The rows are not restored: the mount policy rows carry the level, and a share
    # written after this revision cannot be told apart from a copied one.
    op.create_table(
        "vfolder_permissions",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v7()")),
        sa.Column(
            "permission",
            postgresql.ENUM(name="vfoldermountpermission", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "vfolder",
            GUID,
            sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=False),
    )
