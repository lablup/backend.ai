"""add_extra_column_to_artifacts

Revision ID: 96e9056b8e72
Revises: 5a5142f6d251
Create Date: 2025-11-04 09:51:43.152737

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "96e9056b8e72"
down_revision = "5a5142f6d251"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "artifacts", sa.Column("extra", sa.JSON(none_as_null=True), nullable=True, default=None)
    )


def downgrade() -> None:
    op.drop_column("artifacts", "extra")
