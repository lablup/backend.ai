"""make session idle check expire_at non-nullable

Revision ID: ea422739665b
Revises: a0a28251f296
Create Date: 2026-07-22 15:16:51.824682

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ea422739665b"
down_revision = "a0a28251f296"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_TABLE = "session_idle_checks"


def upgrade() -> None:
    # A missing deadline carries no valid judgment under the new contract. Deleting
    # the row avoids manufacturing a deadline that could terminate the session.
    op.execute(sa.text("DELETE FROM session_idle_checks WHERE expire_at IS NULL"))
    op.alter_column(
        _TABLE,
        "expire_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        _TABLE,
        "expire_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
