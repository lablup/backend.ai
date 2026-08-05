"""add confidential attested guest witness

Revision ID: e3b5c8d1f409
Revises: d2a3b4c5e6f7
Create Date: 2026-08-05

"""

import sqlalchemy as sa
from alembic import op

revision = "e3b5c8d1f409"
down_revision = "d2a3b4c5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "confidential_attested_guests",
        sa.Column("guest", sa.String(length=128), primary_key=True),
        sa.Column("endpoint", sa.String(length=1024), primary_key=True),
        sa.Column(
            "witnessed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("confidential_attested_guests")
