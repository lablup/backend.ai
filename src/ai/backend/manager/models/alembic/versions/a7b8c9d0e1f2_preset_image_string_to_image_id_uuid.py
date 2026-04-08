"""preset image string to image_id uuid

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-04-03

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Clear existing data (new table, no production data)
    op.execute("DELETE FROM deployment_revision_presets")
    op.drop_column("deployment_revision_presets", "image")
    op.add_column(
        "deployment_revision_presets",
        sa.Column(
            "image_id",
            GUID(),
            sa.ForeignKey("images.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("deployment_revision_presets", "image_id")
    op.add_column(
        "deployment_revision_presets",
        sa.Column("image", sa.String(length=512), nullable=True),
    )
