"""remove_keypair_concurrency_used

Revision ID: d59ff89e7514
Revises: 0f7a4b643940
Create Date: 2022-03-21 16:43:29.899251

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd59ff89e7514'
down_revision = '0f7a4b643940'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('keypairs', 'concurrency_used')


def downgrade():
    op.add_column('keypairs', sa.Column(
        'concurrency_used', sa.Integer, nullable=True, default=0, server_default=0,
    ))
