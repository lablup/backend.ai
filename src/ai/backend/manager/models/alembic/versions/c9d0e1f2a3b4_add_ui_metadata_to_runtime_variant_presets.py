"""add ui metadata to runtime_variant_presets

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-04-03

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "runtime_variant_presets",
        sa.Column("category", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column("ui_type", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column("display_name", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "runtime_variant_presets",
        sa.Column("ui_option", pgsql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("runtime_variant_presets", "ui_option")
    op.drop_column("runtime_variant_presets", "display_name")
    op.drop_column("runtime_variant_presets", "ui_type")
    op.drop_column("runtime_variant_presets", "category")
