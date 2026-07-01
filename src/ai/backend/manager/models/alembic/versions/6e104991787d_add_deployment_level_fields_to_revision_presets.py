"""add deployment-level fields to deployment_revision_presets

Revision ID: 6e104991787d
Revises: 689f66507280
Create Date: 2026-04-07

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
# Part of: 26.3.0 (main)
revision = "6e104991787d"
down_revision = "689f66507280"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployment_revision_presets",
        sa.Column("open_to_public", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "deployment_revision_presets",
        sa.Column("replica_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "deployment_revision_presets",
        sa.Column("revision_history_limit", sa.Integer(), nullable=True),
    )
    op.add_column(
        "deployment_revision_presets",
        sa.Column("deployment_strategy", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "deployment_revision_presets",
        sa.Column("deployment_strategy_spec", pgsql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("deployment_revision_presets", "deployment_strategy_spec")
    op.drop_column("deployment_revision_presets", "deployment_strategy")
    op.drop_column("deployment_revision_presets", "revision_history_limit")
    op.drop_column("deployment_revision_presets", "replica_count")
    op.drop_column("deployment_revision_presets", "open_to_public")
