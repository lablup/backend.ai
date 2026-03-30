"""add unique constraint

Revision ID: 9fc0e92ea510
Revises: d537c050dd8d
Create Date: 2025-03-05 10:17:37.646624

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9fc0e92ea510"
down_revision = "d537c050dd8d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_resource_presets_name_null_scaling_group_name",
        "resource_presets",
        ["name"],
        unique=True,
        postgresql_where=sa.text("scaling_group_name IS NULL"),
    )
    op.create_index(
        "ix_resource_presets_name_scaling_group_name",
        "resource_presets",
        ["name", "scaling_group_name"],
        unique=True,
        postgresql_where=sa.text("scaling_group_name IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resource_presets_name_scaling_group_name",
        table_name="resource_presets",
        postgresql_where=sa.text("scaling_group_name IS NOT NULL"),
    )
    op.drop_index(
        "ix_resource_presets_name_null_scaling_group_name",
        table_name="resource_presets",
        postgresql_where=sa.text("scaling_group_name IS NULL"),
    )
