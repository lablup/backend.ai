"""add confidential channel vouching

Revision ID: d2a3b4c5e6f7
Revises: c1f0a7d3b9e2
Create Date: 2026-08-04

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "d2a3b4c5e6f7"
down_revision = "c1f0a7d3b9e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "confidential_channels",
        sa.Column("kernel_id", GUID, primary_key=True),
        sa.Column("session_id", GUID, nullable=False, index=True),
        sa.Column("endpoint", sa.String(length=1024), nullable=False),
        sa.Column("resource_path", sa.String(length=512), nullable=False),
        sa.Column("relay_addr", sa.String(length=256), nullable=False),
        sa.Column("channel_port", sa.Integer, nullable=False),
        sa.Column("fingerprint", sa.String(length=128), nullable=False),
        sa.Column("token", sa.String(length=256), nullable=False),
        sa.Column("epoch", sa.Integer, nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("confidential_channels")
