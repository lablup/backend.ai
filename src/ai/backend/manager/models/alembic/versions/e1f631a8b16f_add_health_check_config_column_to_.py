"""Add health_check_config column to endpoints

Revision ID: e1f631a8b16f
Revises: b0fb0eb6b6bc
Create Date: 2025-12-08 08:38:05.693150

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f631a8b16f"
down_revision = "b0fb0eb6b6bc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoints",
        sa.Column("health_check_config", sa.JSON(none_as_null=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("endpoints", "health_check_config")
