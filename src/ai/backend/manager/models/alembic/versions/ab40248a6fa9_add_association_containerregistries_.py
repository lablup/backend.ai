"""add association `ContainerRegistries` with `Users` table.
Revision ID: c0b46faaa9fe
Revises: 1d42c726d8a3
Create Date: 2024-03-16 19:39:02.043247
"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, IDColumn

# revision identifiers, used by Alembic.
revision = "c0b46faaa9fe"
down_revision = "1d42c726d8a3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "association_container_registries_users",
        IDColumn("id"),
        sa.Column(
            "container_registry_id",
            GUID,
            sa.ForeignKey("container_registries.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            GUID,
            sa.ForeignKey("users.uuid", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("association_container_registries_users")
