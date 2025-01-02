"""add sessions batch_timeout column

Revision ID: d4c174934fd0
Revises: e9e574a6e22d
Create Date: 2024-11-11 16:47:05.150825

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4c174934fd0"
down_revision = "e9e574a6e22d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("batch_timeout", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "batch_timeout")
