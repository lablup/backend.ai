"""add replica group rollout column

Revision ID: 5e5d1672ccc2
Revises: c4e9f2a7b1d8
Create Date: 2026-06-04 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# Part of: 26.6.0

# revision identifiers, used by Alembic.
revision = "5e5d1672ccc2"
down_revision = "c4e9f2a7b1d8"
branch_labels = None
depends_on = None

# Existing replica groups predate explicit rollout config; assume the rolling-update
# baseline (50% surge). New rows always set ``rollout`` explicitly from the strategy.
_EXISTING_ROLLOUT_JSON = (
    '{"max_surge":{"count":null,"percent":0.5},"max_unavailable":{"count":null,"percent":0.0}}'
)


def upgrade() -> None:
    op.add_column(
        "replica_groups",
        sa.Column("rollout", pgsql.JSONB(), nullable=True),
    )
    op.execute(
        sa.text("UPDATE replica_groups SET rollout = CAST(:val AS JSONB)").bindparams(
            val=_EXISTING_ROLLOUT_JSON
        )
    )
    op.alter_column("replica_groups", "rollout", nullable=False)


def downgrade() -> None:
    op.drop_column("replica_groups", "rollout")
