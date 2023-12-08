"""Add dotfile column to keypairs

Revision ID: 1e8531583e20
Revises: ce209920f654
Create Date: 2020-01-17 15:59:09.367691

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1e8531583e20"
down_revision = "ce209920f654"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "keypairs",
        sa.Column(
            "dotfiles", sa.LargeBinary(length=64 * 1024), nullable=False, server_default="\\x90"
        ),
    )


def downgrade():
    op.drop_column("keypairs", "dotfiles")
