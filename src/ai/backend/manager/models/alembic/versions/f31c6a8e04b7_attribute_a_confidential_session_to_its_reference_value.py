"""attribute a confidential session to its reference value

Revision ID: f31c6a8e04b7
Revises: d5b8f2c47a10
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "f31c6a8e04b7"
down_revision = "d5b8f2c47a10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "confidential_attested_guests",
        sa.Column("reference_value_id", GUID, nullable=True),
    )
    op.add_column(
        "confidential_nonces",
        sa.Column("reference_value_id", GUID, nullable=True),
    )
    op.create_index(
        "ix_confidential_nonces_reference_value_id",
        "confidential_nonces",
        ["reference_value_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_confidential_nonces_reference_value_id", "confidential_nonces")
    op.drop_column("confidential_nonces", "reference_value_id")
    op.drop_column("confidential_attested_guests", "reference_value_id")
