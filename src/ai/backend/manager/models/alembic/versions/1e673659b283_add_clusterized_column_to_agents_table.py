"""Add clusterized column to agents table

Revision ID: 1e673659b283
Revises: d5cc54fd36b5
Create Date: 2020-01-07 17:52:51.771357

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1e673659b283"
down_revision = "d5cc54fd36b5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agents", sa.Column("clusterized", sa.Boolean, default=False))


def downgrade():
    op.drop_column("agents", "clusterized")
