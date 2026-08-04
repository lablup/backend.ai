"""add client key release audit and the per-folder encryption tier

Revision ID: d2e4a6c80b57
Revises: d3e1b7a90c4f
Create Date: 2026-08-04

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "d2e4a6c80b57"
down_revision = "d3e1b7a90c4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vfolders", sa.Column("encryption_tier", sa.String(length=32), nullable=True))
    op.create_table(
        "confidential_client_releases",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "released_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
        sa.Column("vfolder_id", GUID, nullable=False, index=True),
        sa.Column("domain_name", sa.String(length=64), nullable=False),
        sa.Column("requester_id", GUID, nullable=False),
        sa.Column("requester", sa.String(length=256), nullable=False),
        sa.Column("session_id", GUID, nullable=True),
        sa.Column("scope", sa.String(length=128), nullable=False),
        sa.Column("tier", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("confidential_client_releases")
    op.drop_column("vfolders", "encryption_tier")
