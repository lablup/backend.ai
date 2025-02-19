"""Add association table with `ContainerRegistries`, and `Groups` table.

Revision ID: 8f85e9d0bd4e
Revises: ecc9f6322be4
Create Date: 2024-11-11 01:59:47.584430

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, IDColumn

# revision identifiers, used by Alembic.
revision = "8f85e9d0bd4e"
down_revision = "ecc9f6322be4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "association_container_registries_groups",
        IDColumn("id"),
        sa.Column(
            "registry_id",
            GUID,
            nullable=False,
        ),
        sa.Column(
            "group_id",
            GUID,
            nullable=False,
        ),
        sa.UniqueConstraint("registry_id", "group_id", name="uq_registry_id_group_id"),
    )


def downgrade() -> None:
    op.drop_table("association_container_registries_groups")
