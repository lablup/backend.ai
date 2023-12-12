"""remove-clusterized

Revision ID: dc9b66466e43
Revises: 06184d82a211
Create Date: 2020-12-25 04:45:20.245137

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dc9b66466e43"
down_revision = "06184d82a211"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("agents", "clusterized")


def downgrade():
    op.add_column(
        "agents", sa.Column("clusterized", sa.BOOLEAN(), autoincrement=False, nullable=True)
    )
