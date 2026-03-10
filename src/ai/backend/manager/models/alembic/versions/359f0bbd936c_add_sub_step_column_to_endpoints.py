"""add sub_step column to endpoints

Revision ID: 359f0bbd936c
Revises: b1009fe7f865
Create Date: 2026-03-09 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "359f0bbd936c"
down_revision = "b1009fe7f865"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoints",
        sa.Column("sub_step", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_endpoints_lifecycle_sub_step",
        "endpoints",
        ["lifecycle_stage", "sub_step"],
    )


def downgrade() -> None:
    op.drop_index("ix_endpoints_lifecycle_sub_step", table_name="endpoints")
    op.drop_column("endpoints", "sub_step")
