"""add the audit_logs client IP column

Revision ID: d7a2f4c86b13
Revises: c4e7a1b93f60
Create Date: 2026-08-24 00:20:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "d7a2f4c86b13"
down_revision = "c4e7a1b93f60"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audit_logs",
        sa.Column("client_ip", pgsql.INET, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("audit_logs", "client_ip")
