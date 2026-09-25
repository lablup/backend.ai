"""Backfill destroyed_at of destroyed endpoints

Endpoints destroyed through the lifecycle handler kept a null destroyed_at, so the
retention sweep never reaches them. Fill each one from the last history row of that
deployment, falling back to the endpoint's own creation time.

Revision ID: d3a7c1e5b904
Revises: c4b1f7e9a2d3
Create Date: 2026-09-22

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d3a7c1e5b904"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c4b1f7e9a2d3"
branch_labels = None
depends_on = None

BACKFILL: Final[str] = """
    UPDATE endpoints e
    SET destroyed_at = COALESCE(
        (
            SELECT MAX(h.updated_at)
            FROM deployment_history h
            WHERE h.deployment_id = e.id
        ),
        e.created_at
    )
    WHERE e.lifecycle_stage = 'destroyed' AND e.destroyed_at IS NULL
"""


def upgrade() -> None:
    op.execute(sa.text(BACKFILL))


def downgrade() -> None:
    # Nothing is reverted: a filled timestamp cannot be told apart from one the
    # lifecycle write stamped.
    pass
