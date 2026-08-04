"""add integrity tier mount leases

Revision ID: d3e1b7a90c4f
Revises: c1f0a7d3b9e2
Create Date: 2026-08-04

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "d3e1b7a90c4f"
down_revision = "c1f0a7d3b9e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integrity_mount_leases",
        sa.Column("folder_id", GUID, primary_key=True),
        sa.Column("holder", GUID, nullable=True),
        sa.Column("epoch", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fence", sa.String(length=32), nullable=False, server_default="released"),
        sa.Column("fence_reason", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("integrity_mount_leases")
