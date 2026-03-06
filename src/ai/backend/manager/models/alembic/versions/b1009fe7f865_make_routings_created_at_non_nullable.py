"""Make routings.created_at non-nullable

Revision ID: b1009fe7f865
Revises: 3f5c20f7bb07
Create Date: 2026-03-06 04:11:09.336691

"""

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b1009fe7f865"
down_revision = "3f5c20f7bb07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fill any existing NULLs with now() before adding NOT NULL constraint
    op.execute("UPDATE routings SET created_at = now() WHERE created_at IS NULL")
    op.alter_column(
        "routings",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default="now()",
    )


def downgrade() -> None:
    op.alter_column(
        "routings",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
        existing_server_default="now()",
    )
