"""add uuid column to resource_slot_types table

Revision ID: 8f21c46a0b73
Revises: c04f8b1a6e37
Create Date: 2026-08-06 10:12:44.813022

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "8f21c46a0b73"
down_revision = "c04f8b1a6e37"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resource_slot_types",
        sa.Column(
            "uuid",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_resource_slot_types_uuid", "resource_slot_types", ["uuid"])


def downgrade() -> None:
    op.drop_constraint("uq_resource_slot_types_uuid", "resource_slot_types", type_="unique")
    op.drop_column("resource_slot_types", "uuid")
