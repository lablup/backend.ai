"""make session idle check expire_at nullable

Revision ID: 890490020974
Revises: e7a41b29c8d3
Create Date: 2026-07-27

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "890490020974"
down_revision = "e7a41b29c8d3"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "session_idle_checks",
        "expire_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM session_idle_checks WHERE expire_at IS NULL"))
    op.alter_column(
        "session_idle_checks",
        "expire_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
