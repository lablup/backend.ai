"""remove unique constraint of endpoints.name

Revision ID: e812d42bc34f
Revises: 02535458c0b3
Create Date: 2023-09-06 19:16:50.916865

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e812d42bc34f"
down_revision = "02535458c0b3"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq_endpoints_name", "endpoints")


def downgrade():
    op.create_unique_constraint("uq_endpoints_name", "endpoints", ["name"])
