"""add created_at to permissions table

Revision ID: cff56a8381dd
Revises: 3727dd0927cf
Create Date: 2026-03-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cff56a8381dd"
down_revision = "3727dd0927cf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "permissions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("permissions", "created_at")
