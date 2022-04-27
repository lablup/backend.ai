"""Add wsproxy_addr column on scaling_group

Revision ID: 60a1effa77d2
Revises: 8679d0a7e22b
Create Date: 2021-09-17 13:19:57.525513

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '60a1effa77d2'
down_revision = '8679d0a7e22b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('scaling_groups', sa.Column('wsproxy_addr', sa.String(length=1024), nullable=True))


def downgrade():
    op.drop_column('scaling_groups', 'wsproxy_addr')
