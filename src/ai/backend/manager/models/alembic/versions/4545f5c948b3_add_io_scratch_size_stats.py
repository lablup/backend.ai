"""add_io_scratch_size_stats

Revision ID: 4545f5c948b3
Revises: e7371ca5797a
Create Date: 2017-10-10 15:57:48.463055

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4545f5c948b3'
down_revision = 'e7371ca5797a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('kernels', sa.Column('io_max_scratch_size', sa.BigInteger(), nullable=True))
    op.drop_column('kernels', 'mem_cur_bytes')


def downgrade():
    op.add_column('kernels', sa.Column('mem_cur_bytes', sa.BIGINT(), autoincrement=False, nullable=True))
    op.drop_column('kernels', 'io_max_scratch_size')
