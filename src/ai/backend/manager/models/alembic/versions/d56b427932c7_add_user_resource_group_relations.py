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
        "user_resource_group_relations",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("resource_group_id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["resource_group_id"],
            ["scaling_groups.id"],
            name="fk_user_resource_group_relations_resource_group_id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name="fk_user_resource_group_relations_user_id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_resource_group_relations")),
        sa.UniqueConstraint(
            "resource_group_id",
            "user_id",
            name=op.f("uq_user_resource_group_relations_resource_group_id"),
        ),
    )
    op.create_index(
        op.f("ix_user_resource_group_relations_resource_group_id"),
        "user_resource_group_relations",
        ["resource_group_id"],
    )
    op.create_index(
        op.f("ix_user_resource_group_relations_user_id"),
        "user_resource_group_relations",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_table("user_resource_group_relations")
