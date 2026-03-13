"""Add server_default to roles.updated_at

Revision ID: df13b2272b61
Revises: 6f2f5d828a52
Create Date: 2026-03-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "df13b2272b61"
down_revision = "6f2f5d828a52"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Backfill NULL updated_at values with created_at
    conn.execute(
        text(
            """\
        UPDATE roles
        SET updated_at = created_at
        WHERE updated_at IS NULL;
    """
        )
    )

    # Alter column to add server_default and make non-nullable
    op.alter_column(
        "roles",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    )


def downgrade() -> None:
    # Revert to nullable and remove server_default
    op.alter_column(
        "roles",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
        server_default=None,
    )
