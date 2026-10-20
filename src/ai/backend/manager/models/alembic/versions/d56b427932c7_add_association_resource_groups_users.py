"""Add the table linking resource groups to users

Revision ID: d56b427932c7
Revises: e234d84a162f
Create Date: 2026-10-20

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "d56b427932c7"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e234d84a162f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "association_resource_groups_users",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("resource_group_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["resource_group_id"],
            ["scaling_groups.id"],
            name="fk_association_resource_groups_users_resource_group_id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name="fk_association_resource_groups_users_user_id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_association_resource_groups_users")),
        sa.UniqueConstraint(
            "resource_group_id",
            "user_id",
            name=op.f("uq_association_resource_groups_users_resource_group_id"),
        ),
    )
    op.create_index(
        op.f("ix_association_resource_groups_users_resource_group_id"),
        "association_resource_groups_users",
        ["resource_group_id"],
    )
    op.create_index(
        op.f("ix_association_resource_groups_users_user_id"),
        "association_resource_groups_users",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_table("association_resource_groups_users")
