"""add nullable usage bucket resource_group_id columns

Add nullable ``resource_group_id`` columns alongside the existing
``resource_group`` name columns and backfill rows whose names still resolve.
Name-based constraints and lookup behavior remain unchanged during this
expand phase.

Revision ID: 7a9720934f55
Revises: 710460cca1ed
Create Date: 2026-07-14

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "7a9720934f55"
down_revision = "710460cca1ed"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "domain_usage_buckets",
        sa.Column("resource_group_id", GUID(), nullable=True),
    )
    op.execute(
        """
        UPDATE domain_usage_buckets
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE domain_usage_buckets.resource_group = scaling_groups.name
          AND domain_usage_buckets.resource_group_id IS NULL
        """
    )
    op.add_column(
        "project_usage_buckets",
        sa.Column("resource_group_id", GUID(), nullable=True),
    )
    op.execute(
        """
        UPDATE project_usage_buckets
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE project_usage_buckets.resource_group = scaling_groups.name
          AND project_usage_buckets.resource_group_id IS NULL
        """
    )
    op.add_column(
        "user_usage_buckets",
        sa.Column("resource_group_id", GUID(), nullable=True),
    )
    op.execute(
        """
        UPDATE user_usage_buckets
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE user_usage_buckets.resource_group = scaling_groups.name
          AND user_usage_buckets.resource_group_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("user_usage_buckets", "resource_group_id")
    op.drop_column("project_usage_buckets", "resource_group_id")
    op.drop_column("domain_usage_buckets", "resource_group_id")
