"""add nullable kernel usage record resource_group_id column

Add a nullable ``resource_group_id`` column alongside the existing
``resource_group`` name column and backfill rows whose names still resolve.
The name-based lookup behavior remains unchanged during this expand phase.

Revision ID: 710460cca1ed
Revises: 097389c0853b
Create Date: 2026-07-14

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "710460cca1ed"
down_revision = "097389c0853b"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("kernel_usage_records", sa.Column("resource_group_id", GUID(), nullable=True))
    op.execute(
        """
        UPDATE kernel_usage_records
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE kernel_usage_records.resource_group = scaling_groups.name
          AND kernel_usage_records.resource_group_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("kernel_usage_records", "resource_group_id")
