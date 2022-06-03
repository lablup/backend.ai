"""add_environ_to_kernels

Revision ID: c3e74dcf1808
Revises: d52bf5ec9ef3
Create Date: 2017-11-15 11:31:54.083566

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3e74dcf1808'
down_revision = 'd52bf5ec9ef3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('kernels', sa.Column('environ', sa.ARRAY(sa.String()), nullable=True))


def downgrade():
    op.drop_column('kernels', 'environ')
