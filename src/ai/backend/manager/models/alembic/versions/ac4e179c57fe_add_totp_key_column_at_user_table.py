"""add totp_key column at user table

Revision ID: ac4e179c57fe
Revises: cace152eefac
Create Date: 2023-02-17 11:54:50.930903

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ac4e179c57fe"
down_revision = "cace152eefac"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("totp_key", sa.CHAR(32), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "totp_activated", sa.Boolean, nullable=False, server_default="false", default=False
        ),
    )


def downgrade():
    op.drop_column("users", "totp_activated")
    op.drop_column("users", "totp_key")
