"""add-callback_url-to-kernels

Revision ID: d727b5da20e6
Revises: a7ca9f175d5f
Create Date: 2022-03-31 07:22:28.426046

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import URLColumn

# revision identifiers, used by Alembic.
revision = "d727b5da20e6"
down_revision = "a7ca9f175d5f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("kernels", sa.Column("callback_url", URLColumn(), nullable=True))


def downgrade():
    op.drop_column("kernels", "callback_url")
