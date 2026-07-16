"""add nullable fair-share resource_group_id columns

Add nullable ``resource_group_id`` columns alongside the existing
``resource_group`` name columns and backfill rows whose names still resolve.
Name-based constraints and lookup behavior remain unchanged during this
expand phase.

Revision ID: 097389c0853b
Revises: c4e1a9b73f52
Create Date: 2026-07-09

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "097389c0853b"
down_revision = "c4e1a9b73f52"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "domain_fair_shares",
        sa.Column("resource_group_id", GUID(), nullable=True),
    )
    op.execute(
        """
        UPDATE domain_fair_shares
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE domain_fair_shares.resource_group = scaling_groups.name
          AND domain_fair_shares.resource_group_id IS NULL
        """
    )
    op.add_column(
        "project_fair_shares",
        sa.Column("resource_group_id", GUID(), nullable=True),
    )
    op.execute(
        """
        UPDATE project_fair_shares
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE project_fair_shares.resource_group = scaling_groups.name
          AND project_fair_shares.resource_group_id IS NULL
        """
    )
    op.add_column(
        "user_fair_shares",
        sa.Column("resource_group_id", GUID(), nullable=True),
    )
    op.execute(
        """
        UPDATE user_fair_shares
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE user_fair_shares.resource_group = scaling_groups.name
          AND user_fair_shares.resource_group_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("user_fair_shares", "resource_group_id")
    op.drop_column("project_fair_shares", "resource_group_id")
    op.drop_column("domain_fair_shares", "resource_group_id")
