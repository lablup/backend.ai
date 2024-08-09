"""add-agent-public-key

Revision ID: 97d8c7aa5e96
Revises: 4871d46ba31b
Create Date: 2023-09-15 16:09:14.824019

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "97d8c7aa5e96"
down_revision = "4871d46ba31b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agents", sa.Column("public_key", sa.String(length=40), nullable=True))


def downgrade():
    op.drop_column("agents", "public_key")
