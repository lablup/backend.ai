"""add_extra_column_to_artifacts

Revision ID: 96e9056b8e72
Revises: d811b103dbfc
Create Date: 2025-11-04 09:51:43.152737

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "96e9056b8e72"
down_revision = "d811b103dbfc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add extra column to artifacts table
    op.add_column("artifacts", sa.Column("extra", sa.JSON, nullable=True, default=None))


def downgrade() -> None:
    # Remove extra column from artifacts table
    op.drop_column("artifacts", "extra")
