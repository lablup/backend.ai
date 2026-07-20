"""add category table and description/rank/category_id to presets

Revision ID: a3b4c5d6e7f8
Revises: 89a57e90f3b4
Create Date: 2026-04-14

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "a3b4c5d6e7f8"
down_revision = "89a57e90f3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prometheus_query_preset_categories",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        "prometheus_query_presets",
        sa.Column("description", sa.Text, nullable=True),
    )
    op.add_column(
        "prometheus_query_presets",
        sa.Column("rank", sa.Integer, nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "prometheus_query_presets",
        sa.Column("category_id", GUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_prometheus_query_presets_category_id",
        "prometheus_query_presets",
        "prometheus_query_preset_categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_prometheus_query_presets_category_id",
        "prometheus_query_presets",
        ["category_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_prometheus_query_presets_category_id", table_name="prometheus_query_presets")
    op.drop_column("prometheus_query_presets", "category_id")
    op.drop_column("prometheus_query_presets", "rank")
    op.drop_column("prometheus_query_presets", "description")
    op.drop_table("prometheus_query_preset_categories")
