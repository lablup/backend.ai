"""add worker.reject_brotli_request_body

Revision ID: 96232dc81c6a
Revises: a1b2c3d4e5f6
Create Date: 2026-10-26 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "96232dc81c6a"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    columns = [c["name"] for c in sa.inspect(conn).get_columns("workers")]
    if "reject_brotli_request_body" not in columns:
        op.add_column(
            "workers",
            sa.Column(
                "reject_brotli_request_body",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    op.execute("ALTER TABLE workers DROP COLUMN IF EXISTS reject_brotli_request_body")
