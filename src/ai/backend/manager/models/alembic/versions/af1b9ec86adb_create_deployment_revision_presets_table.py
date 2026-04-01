"""create deployment_revision_presets table

Revision ID: af1b9ec86adb
Revises: ed1aa96c40d0
Create Date: 2026-04-01

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import GUID, IDColumn

# revision identifiers, used by Alembic.
revision = "af1b9ec86adb"
down_revision = "ed1aa96c40d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deployment_revision_presets",
        IDColumn(),
        sa.Column(
            "runtime_variant",
            GUID(),
            sa.ForeignKey("runtime_variants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("image", sa.String(length=512), nullable=True),
        sa.Column("model_definition", pgsql.JSONB(), nullable=True),
        sa.Column("resource_slots", pgsql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("resource_opts", pgsql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "cluster_mode", sa.String(length=16), nullable=False, server_default="single-node"
        ),
        sa.Column("cluster_size", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("startup_command", sa.Text(), nullable=True),
        sa.Column("bootstrap_script", sa.Text(), nullable=True),
        sa.Column("environ", pgsql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("preset_values", pgsql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deployment_revision_presets")),
        sa.UniqueConstraint(
            "runtime_variant", "name", name=op.f("uq_deployment_revision_presets_variant_name")
        ),
        sa.Index("ix_deployment_revision_presets_variant_rank", "runtime_variant", "rank"),
    )


def downgrade() -> None:
    op.drop_table("deployment_revision_presets")
