"""add server_default to images.last_used_at

Revision ID: f7d3738a3cef
Revises: c7f2a8e31b04
Create Date: 2026-04-14

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f7d3738a3cef"
down_revision = "c7f2a8e31b04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns("images")
    for col in columns:
        if col["name"] == "last_used_at":
            if col.get("default") is not None:
                return
            break
    else:
        return

    op.alter_column(
        "images",
        "last_used_at",
        server_default=sa.func.now(),
    )


def downgrade() -> None:
    op.alter_column(
        "images",
        "last_used_at",
        server_default=None,
    )
