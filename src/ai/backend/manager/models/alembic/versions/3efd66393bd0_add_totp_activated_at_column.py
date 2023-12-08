"""add totp_activated_at column

Revision ID: 3efd66393bd0
Revises: ac4e179c57fe
Create Date: 2023-02-18 23:50:57.504752

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3efd66393bd0"
down_revision = "ac4e179c57fe"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("totp_activated_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade():
    op.drop_column("users", "totp_activated_at")
