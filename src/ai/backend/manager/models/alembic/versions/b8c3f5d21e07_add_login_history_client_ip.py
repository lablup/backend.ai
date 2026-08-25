"""add the login_history client IP column

Revision ID: b8c3f5d21e07
Revises: a3f1c7d92b04
Create Date: 2026-08-24 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "b8c3f5d21e07"
down_revision = "a3f1c7d92b04"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "login_history",
        sa.Column("client_ip", pgsql.INET, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("login_history", "client_ip")
