"""add worker upstream tls capability

Revision ID: f3c7d9e1a2b4
Revises: a1b2c3d4e5f6
Create Date: 2026-08-04

"""

import sqlalchemy as sa
from alembic import op

revision = "f3c7d9e1a2b4"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workers",
        sa.Column(
            "upstream_tls_capable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("workers", "upstream_tls_capable")
