"""add the client IP masking policies table

Revision ID: c4e7a1b93f60
Revises: b8c3f5d21e07
Create Date: 2026-08-24 00:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.models.base import GUID, StrEnumType

# revision identifiers, used by Alembic.
revision = "c4e7a1b93f60"
down_revision = "b8c3f5d21e07"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_ip_masking_policies",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("target_type", StrEnumType(ClientIPMaskingTarget), nullable=False),
        sa.Column("mode", StrEnumType(ClientIPMaskingMode), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("target_type", name="uq_client_ip_masking_policies_target_type"),
    )


def downgrade() -> None:
    op.drop_table("client_ip_masking_policies")
