"""add access_level to model_cards

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-04-02

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "model_cards",
        sa.Column(
            "access_level",
            sa.String(length=32),
            nullable=False,
            server_default="internal",
        ),
    )


def downgrade() -> None:
    op.drop_column("model_cards", "access_level")
