"""add-session_creation_id

Revision ID: 06184d82a211
Revises: 250e8656cf45
Create Date: 2020-12-24 19:58:44.515321

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06184d82a211'
down_revision = '250e8656cf45'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('kernels', sa.Column('session_creation_id', sa.String(length=32), nullable=True))


def downgrade():
    op.drop_column('kernels', 'session_creation_id')
