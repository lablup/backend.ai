"""create kernels.status_history column

Revision ID: 35923972eddb
Revises: 81c264528f20
Create Date: 2022-06-23 17:52:39.307819

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "35923972eddb"
down_revision = "81c264528f20"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "kernels", sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null())
    )


def downgrade():
    op.drop_column("kernels", "status_history")
