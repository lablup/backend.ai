"""add_prometheus_query_presets_table

Revision ID: 32ad43817452
Revises: ffcf0ed13a26
Create Date: 2026-02-24 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "32ad43817452"
down_revision = "ffcf0ed13a26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prometheus_query_presets",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("metric_name", sa.String(length=256), nullable=False),
        sa.Column("query_template", sa.Text(), nullable=False),
        sa.Column("time_window", sa.String(length=32), nullable=True),
        sa.Column(
            "options",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text('\'{"filter_labels":[],"group_labels":[]}\'::jsonb'),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prometheus_query_presets")),
    )
    op.create_index(
        op.f("ix_prometheus_query_presets_name"),
        "prometheus_query_presets",
        ["name"],
    )
    op.create_index(
        op.f("ix_prometheus_query_presets_metric_name"),
        "prometheus_query_presets",
        ["metric_name"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_prometheus_query_presets_metric_name"),
        table_name="prometheus_query_presets",
        if_exists=True,
    )
    op.drop_index(
        op.f("ix_prometheus_query_presets_name"),
        table_name="prometheus_query_presets",
        if_exists=True,
    )
    op.drop_table("prometheus_query_presets")
