"""add prometheus_query_preset_id to endpoint_auto_scaling_rules

Revision ID: ecc4b93d7907
Revises: be1ac9308056
Create Date: 2026-04-10

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ecc4b93d7907"
down_revision = "be1ac9308056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoint_auto_scaling_rules",
        sa.Column(
            "prometheus_query_preset_id",
            GUID(),
            sa.ForeignKey("prometheus_query_presets.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("endpoint_auto_scaling_rules", "prometheus_query_preset_id")
