"""add-service-ports

Revision ID: 0e558d06e0e3
Revises: 10e39a34eed5
Create Date: 2018-12-13 17:39:35.573747

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e558d06e0e3'
down_revision = '10e39a34eed5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('kernels', sa.Column('service_ports', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('kernels', 'service_ports')
