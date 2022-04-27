"""Add logs column on kernel table

Revision ID: 51dddd79aa21
Revises: 3bb80d1887d6
Create Date: 2020-02-11 14:45:55.496745

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51dddd79aa21'
down_revision = '3bb80d1887d6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('kernels', sa.Column('container_log', sa.LargeBinary(), nullable=True))


def downgrade():
    op.drop_column('kernels', 'container_log')
