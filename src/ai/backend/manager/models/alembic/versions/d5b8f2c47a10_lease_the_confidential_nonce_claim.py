"""lease the confidential nonce claim

Revision ID: d5b8f2c47a10
Revises: a7c4e91b2d63
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op

revision = "d5b8f2c47a10"
down_revision = "a7c4e91b2d63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("confidential_nonces", "claims_used")
    op.add_column(
        "confidential_guest_claims",
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.alter_column("confidential_guest_claims", "expires_at", server_default=None)
    op.create_index(
        "ix_confidential_guest_claims_expires_at",
        "confidential_guest_claims",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_confidential_guest_claims_expires_at", "confidential_guest_claims")
    op.drop_column("confidential_guest_claims", "expires_at")
    op.add_column(
        "confidential_nonces",
        sa.Column("claims_used", sa.Integer, nullable=False, server_default=sa.text("0")),
    )
