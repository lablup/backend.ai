"""Add mount_map column to kernel

Revision ID: d452bacd085c
Revises: 4b7b650bc30e
Create Date: 2019-11-19 14:43:12.728678

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql


# revision identifiers, used by Alembic.
revision = 'd452bacd085c'
down_revision = '4b7b650bc30e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('kernels', sa.Column('mount_map', pgsql.JSONB(), nullable=True, default={}))


def downgrade():
    op.drop_column('kernels', 'mount_map')

