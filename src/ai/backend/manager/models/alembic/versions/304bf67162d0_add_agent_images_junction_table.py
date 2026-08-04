"""add agent_images junction table

Records which images are installed on which agents.

Revision ID: 304bf67162d0
Revises: 1e088322c207
Create Date: 2026-08-04 11:52:45.315444

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "304bf67162d0"
down_revision = "1e088322c207"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_images",
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("image_id", GUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("agent_id", "image_id", name=op.f("pk_agent_images")),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name=op.f("fk_agent_images_agent_id_agents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["image_id"],
            ["images.id"],
            name=op.f("fk_agent_images_image_id_images"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_agent_images_image_id"), "agent_images", ["image_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_images_image_id"), table_name="agent_images")
    op.drop_table("agent_images")
