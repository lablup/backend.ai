"""replace vfolders.permission with default_mount_permission

The column is the folder's default mount level. It kept its legacy name and value set,
and session mounts never read it. It becomes ``default_mount_permission`` with the
values ``none``, ``ro`` and ``rw``: a project folder keeps its value (``wd`` folds to
``rw``), a personal folder becomes ``none`` because its owner mounts regardless and
everyone else needs a per-user policy.

Revision ID: d4a7c2e9f018
Revises: c3f8a1d6e920
Create Date: 2026-09-16

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d4a7c2e9f018"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e7d2a9c41b60"
branch_labels = None
depends_on = None

FILL_DEFAULT_MOUNT_PERMISSION: Final = sa.text("""
    UPDATE vfolders SET default_mount_permission = CASE
        WHEN ownership_type = 'user' THEN 'none'
        WHEN permission = 'ro' THEN 'ro'
        ELSE 'rw'
    END
""")

RESTORE_PERMISSION: Final = sa.text("""
    UPDATE vfolders SET permission = CASE
        WHEN default_mount_permission = 'ro' THEN 'ro'::vfoldermountpermission
        ELSE 'rw'::vfoldermountpermission
    END
""")


def upgrade() -> None:
    op.add_column(
        "vfolders",
        sa.Column("default_mount_permission", sa.String(length=64), nullable=True),
    )
    op.execute(FILL_DEFAULT_MOUNT_PERMISSION)
    op.alter_column("vfolders", "default_mount_permission", nullable=False)
    op.drop_column("vfolders", "permission")


def downgrade() -> None:
    op.add_column(
        "vfolders",
        sa.Column(
            "permission",
            postgresql.ENUM(name="vfoldermountpermission", create_type=False),
            nullable=True,
        ),
    )
    op.execute(RESTORE_PERMISSION)
    op.drop_column("vfolders", "default_mount_permission")
