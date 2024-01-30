"""add architecture column on agents

Revision ID: 911023380bc9
Revises: 015d84d5a5ef
Create Date: 2022-02-16 00:54:23.261212

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "911023380bc9"
down_revision = "015d84d5a5ef"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agents", sa.Column("architecture", sa.String, default="x86_64"))
    op.execute(text("UPDATE agents SET architecture='x86_64'"))
    op.alter_column("agents", "architecture", nullable=False)
    op.add_column("kernels", sa.Column("architecture", sa.String, default="x86_64"))
    op.execute(text("UPDATE kernels SET architecture='x86_64'"))
    op.alter_column("kernels", "architecture", nullable=False)


def downgrade():
    op.drop_column("kernels", "architecture")
    op.drop_column("agents", "architecture")
