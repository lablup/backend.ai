"""add-kernel-host

Revision ID: bf4bae8f942e
Revises: babc74594aa6
Create Date: 2018-02-02 11:29:38.752576

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf4bae8f942e'
down_revision = 'babc74594aa6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('kernels', sa.Column('kernel_host', sa.String(length=128), nullable=True))


def downgrade():
    op.drop_column('kernels', 'kernel_host')
