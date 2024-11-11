"""add sessions batch_timeout column

Revision ID: 8b7d5d2c2163
Revises: e9e574a6e22d
Create Date: 2024-11-11 13:50:02.381335

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8b7d5d2c2163"
down_revision = "e9e574a6e22d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("batch_timeout", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "batch_timeout")
