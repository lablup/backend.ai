"""add creator_id to vfolders

Revision ID: b4e7f1a2c3d5
Revises: a3b7c9d1e5f2
Create Date: 2026-04-14 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "b4e7f1a2c3d5"
down_revision = "a3b7c9d1e5f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vfolders",
        sa.Column("creator_id", GUID, nullable=True),
    )
    op.create_index(
        op.f("ix_vfolders_creator_id"),
        "vfolders",
        ["creator_id"],
        unique=False,
    )
    # Backfill creator_id from users table by matching creator (email) → users.email
    op.execute(
        sa.text(
            "UPDATE vfolders SET creator_id = u.uuid FROM users u WHERE vfolders.creator = u.email"
        )
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_vfolders_creator_id"), table_name="vfolders")
    op.drop_column("vfolders", "creator_id")
