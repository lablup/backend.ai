"""add scaling_group_name column to resource_presets table

Revision ID: d537c050dd8d
Revises: c002140f14d3
Create Date: 2025-02-16 18:20:18.694834

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "d537c050dd8d"
down_revision = "c002140f14d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add scaling_group_name column
    op.add_column(
        "resource_presets",
        sa.Column(
            "scaling_group_name",
            sa.String(length=64),
            server_default=sa.text("NULL"),
            nullable=True,
        ),
    )

    # Migrate primary key from `name` to `id`
    op.drop_constraint(op.f("pk_resource_presets"), "resource_presets", type_="primary")
    op.add_column(
        "resource_presets",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
    )
    op.create_primary_key("pk_resource_presets", "resource_presets", ["id"])


def downgrade() -> None:
    op.drop_column("resource_presets", "scaling_group_name")

    op.drop_column("resource_presets", "id")
    # The resource_presets.name column lacks a unique/primary key constraint. Creation
    # of a primary key may fail if duplicate names exist. Manually resolve any duplicate
    # resource_preset names before retrying.
    op.create_primary_key("pk_resource_presets", "resource_presets", ["name"])
