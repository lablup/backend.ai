"""add replica group status columns

Revision ID: 63be6b4add67
Revises: 3f8a1c6b2e94
Create Date: 2026-06-01 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# Part of: 26.6.0

# revision identifiers, used by Alembic.
revision = "63be6b4add67"
down_revision = "3f8a1c6b2e94"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "replica_groups",
        sa.Column(
            "lifecycle",
            sa.String(length=64),
            nullable=False,
            server_default="stable",
        ),
    )
    op.add_column(
        "replica_groups",
        sa.Column(
            "scaling_status",
            sa.String(length=64),
            nullable=False,
            server_default="stable",
        ),
    )


def downgrade() -> None:
    op.drop_column("replica_groups", "scaling_status")
    op.drop_column("replica_groups", "lifecycle")
