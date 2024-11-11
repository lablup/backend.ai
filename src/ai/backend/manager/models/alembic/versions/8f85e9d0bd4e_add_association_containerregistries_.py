"""Add association table with `ContainerRegistries`, and `Groups` table.

Revision ID: 8f85e9d0bd4e
Revises: e9e574a6e22d
Create Date: 2024-11-11 01:59:47.584430

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, IDColumn

# revision identifiers, used by Alembic.
revision = "8f85e9d0bd4e"
down_revision = "e9e574a6e22d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "association_container_registries_groups",
        IDColumn("id"),
        sa.Column(
            "container_registry_id",
            GUID,
            sa.ForeignKey("container_registries.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "group_id",
            GUID,
            sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("association_container_registries_groups")
