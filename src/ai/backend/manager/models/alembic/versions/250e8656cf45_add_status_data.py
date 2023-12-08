"""add-status_data

Revision ID: 250e8656cf45
Revises: 57e717103287
Create Date: 2020-12-23 14:19:08.801283

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "250e8656cf45"
down_revision = "57e717103287"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "kernels", sa.Column("status_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )


def downgrade():
    op.drop_column("kernels", "status_data")
