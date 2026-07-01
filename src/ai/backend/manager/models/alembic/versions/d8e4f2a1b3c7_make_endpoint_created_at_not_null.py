"""make endpoint created_at columns NOT NULL

Revision ID: d8e4f2a1b3c7
Revises: a3b4c5d6e7f8
Create Date: 2026-04-15

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d8e4f2a1b3c7"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None

_TABLES = ["endpoints", "endpoint_tokens", "endpoint_auto_scaling_rules"]


def upgrade() -> None:
    conn = op.get_bind()
    for table in _TABLES:
        # Backfill any NULLs (should be none due to server_default, but be safe)
        conn.execute(sa.text(f"UPDATE {table} SET created_at = now() WHERE created_at IS NULL"))
        op.alter_column(
            table,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            existing_server_default="now()",
        )


def downgrade() -> None:
    for table in _TABLES:
        op.alter_column(
            table,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
            existing_server_default="now()",
        )
