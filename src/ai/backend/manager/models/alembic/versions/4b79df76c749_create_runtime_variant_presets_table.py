"""create runtime_variant_presets table

Revision ID: 4b79df76c749
Revises: 9229f72fa447
Create Date: 2026-03-31

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID, IDColumn

# revision identifiers, used by Alembic.
revision = "4b79df76c749"
down_revision = "9229f72fa447"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_variant_presets",
        IDColumn(),
        sa.Column(
            "runtime_variant",
            GUID(),
            sa.ForeignKey("runtime_variants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("preset_target", sa.String(length=16), nullable=False),
        sa.Column("value_type", sa.String(length=16), nullable=False),
        sa.Column("default_value", sa.String(length=512), nullable=True),
        sa.Column("key", sa.String(length=256), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_runtime_variant_presets")),
        sa.UniqueConstraint(
            "runtime_variant", "name", name=op.f("uq_runtime_variant_presets_variant_name")
        ),
        sa.Index("ix_runtime_variant_presets_variant_rank", "runtime_variant", "rank"),
    )


def downgrade() -> None:
    op.drop_table("runtime_variant_presets")
