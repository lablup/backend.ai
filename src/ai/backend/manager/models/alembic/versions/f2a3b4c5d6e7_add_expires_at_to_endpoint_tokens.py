"""add expires_at to endpoint_tokens

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-05

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoint_tokens",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("endpoint_tokens", "expires_at")
