"""Add project column to image table

Revision ID: 7c8501cec07b
Revises: 1d42c726d8a3
Create Date: 2024-08-10 07:29:39.492116

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7c8501cec07b"
down_revision = "1d42c726d8a3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("images", sa.Column("project", sa.String, nullable=False))
    # TODO
    # We also need to fill the project column.


def downgrade():
    op.drop_column("images", "project")
