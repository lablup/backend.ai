"""add max_priority to keypair_resource_policies

Revision ID: c4e1a7f9b26d
Revises: 5405ee0d8eed
Create Date: 2026-07-26 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.common.defs.session import SESSION_PRIORITY_MAX, SESSION_PRIORITY_MIN

# revision identifiers, used by Alembic.
revision = "c4e1a7f9b26d"
down_revision = "5405ee0d8eed"
# Part of: "26.8.0"
branch_labels = None
depends_on = None

_TABLE = "keypair_resource_policies"
_RANGE_CHECK = "max_priority_within_session_priority_range"


def upgrade() -> None:
    op.add_column(
        _TABLE,
        sa.Column("max_priority", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        _RANGE_CHECK,
        _TABLE,
        f"max_priority >= {SESSION_PRIORITY_MIN} AND max_priority <= {SESSION_PRIORITY_MAX}",
    )


def downgrade() -> None:
    op.drop_constraint(_RANGE_CHECK, _TABLE, type_="check")
    op.drop_column(_TABLE, "max_priority")
