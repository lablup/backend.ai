"""add the client IP masking policies table

Revision ID: c4e7a1b93f60
Revises: b8c3f5d21e07
Create Date: 2026-08-24 00:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.data.client_ip.masking import (
    MAX_IPV4_PREFIX,
    MAX_IPV6_PREFIX,
    ClientIPMaskingMode,
    ClientIPMaskingTarget,
)
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
        sa.Column("ipv4_prefix", sa.SmallInteger, nullable=True),
        sa.Column("ipv6_prefix", sa.SmallInteger, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("target_type", name="uq_client_ip_masking_policies_target_type"),
        sa.CheckConstraint(
            f"ipv4_prefix IS NULL OR (ipv4_prefix BETWEEN 0 AND {MAX_IPV4_PREFIX})",
            name="ck_client_ip_masking_policies_ipv4_prefix",
        ),
        sa.CheckConstraint(
            f"ipv6_prefix IS NULL OR (ipv6_prefix BETWEEN 0 AND {MAX_IPV6_PREFIX})",
            name="ck_client_ip_masking_policies_ipv6_prefix",
        ),
    )


def downgrade() -> None:
    op.drop_table("client_ip_masking_policies")
