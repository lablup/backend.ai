"""add-kernels-uuid-prefix-index

Revision ID: f5530eccf202
Revises: ed666f476f39
Create Date: 2020-03-25 17:29:50.696450

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5530eccf202'
down_revision = 'ed666f476f39'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        op.f('ix_kernels_uuid_prefix'),
        'kernels',
        [sa.text('CAST("id" AS VARCHAR) COLLATE "C"')],
    )


def downgrade():
    op.drop_index(
        op.f('ix_kernels_uuid_prefix'),
        'kernels',
    )
