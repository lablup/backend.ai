"""add tenant launch credentials

Revision ID: a4c7e1b09d33
Revises: b8e2d4f60a91
Create Date: 2026-08-06 11:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "a4c7e1b09d33"
down_revision = "b8e2d4f60a91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "confidential_launch_credentials",
        sa.Column("nonce", sa.String(length=128), primary_key=True),
        sa.Column("endpoint", sa.String(length=1024), nullable=False),
        sa.Column("domain_name", sa.String(length=64), nullable=False),
        sa.Column("image_digest", sa.String(length=256), nullable=False),
        sa.Column("quota", sa.Integer, nullable=False),
        sa.Column("signature", sa.Text, nullable=False),
        sa.Column(
            "deposited_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("spent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_id", GUID, nullable=True),
    )
    op.create_index(
        "ix_conf_launch_credential_unspent",
        "confidential_launch_credentials",
        ["endpoint", "domain_name", "image_digest", "quota"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conf_launch_credential_unspent", table_name="confidential_launch_credentials"
    )
    op.drop_table("confidential_launch_credentials")
