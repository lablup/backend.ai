"""add-max-session-lifetime

Revision ID: 81c264528f20
Revises: d727b5da20e6
Create Date: 2022-04-21 09:22:01.405710

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '81c264528f20'
down_revision = 'd727b5da20e6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('keypair_resource_policies', sa.Column('max_session_lifetime', sa.Integer(), server_default=sa.text('0'), nullable=False))


def downgrade():
    op.drop_column('keypair_resource_policies', 'max_session_lifetime')
