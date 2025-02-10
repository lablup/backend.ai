"""Add `status` Column to the `Image` table

Revision ID: c002140f14d3
Revises: ecc9f6322be4
Create Date: 2025-02-10 03:22:31.611405

"""

import enum

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import StrEnumType

# revision identifiers, used by Alembic.
revision = "c002140f14d3"
down_revision = "ecc9f6322be4"
branch_labels = None
depends_on = None


class ImageStatus(enum.StrEnum):
    ALIVE = "ALIVE"
    DELETED = "DELETED"


def upgrade() -> None:
    op.add_column(
        "images",
        sa.Column(
            "status", StrEnumType(ImageStatus), server_default=ImageStatus.ALIVE, nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("images", "status")
