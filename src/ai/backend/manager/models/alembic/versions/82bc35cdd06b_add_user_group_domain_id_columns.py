"""add user/group domain_id columns

Add ``domain_id`` columns alongside the existing ``domain_name`` columns and
backfill them from ``domains``. Groups whose domain no longer resolves are
dropped and ``groups.domain_id`` becomes NOT NULL; ``users.domain_id`` stays
nullable (mirroring ``users.domain_name``). Name-based FKs and lookups remain
unchanged during this expand phase.

Revision ID: 82bc35cdd06b
Revises: b93d1c47af52
Create Date: 2026-07-31

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "82bc35cdd06b"
down_revision = "857c4d02c4b9"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("domain_id", GUID(), nullable=True))
    op.execute(
        """
        UPDATE users
        SET domain_id = domains.id
        FROM domains
        WHERE users.domain_name = domains.name
          AND users.domain_id IS NULL
        """
    )
    op.add_column("groups", sa.Column("domain_id", GUID(), nullable=True))
    op.execute(
        """
        UPDATE groups
        SET domain_id = domains.id
        FROM domains
        WHERE groups.domain_name = domains.name
          AND groups.domain_id IS NULL
        """
    )
    op.execute("DELETE FROM groups WHERE domain_id IS NULL")
    op.alter_column("groups", "domain_id", nullable=False)


def downgrade() -> None:
    op.drop_column("groups", "domain_id")
    op.drop_column("users", "domain_id")
