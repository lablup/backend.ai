"""Stamp the retention boundary on the session groups no replica group serves

The retention sweep collected session groups on created_at, so a group still owned by
an active deployment disappeared once the deployments retention period passed. The
boundary is now deleted_at, which the lifecycle applier stamps when a replica group
reaches a terminal lifecycle and the endpoint destroy path when it retires the groups.
A group whose replica group is already terminal is filled here so the sweep still
reaches it. A group with a live replica group keeps a NULL boundary and survives.

A group no replica group ever referenced is left alone: it belongs to a user, not a
deployment, and stamping it would recreate the reported symptom. A group whose replica
group was purged before this revision is indistinguishable from that case and stays
uncollected.

Revision ID: afcdb49cc729
Revises: ece8800e945c
Create Date: 2026-11-04

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "afcdb49cc729"
down_revision = "ece8800e945c"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

# The EXISTS narrows the backfill to groups a deployment actually owned. A group with
# no replica group at all is a user group; it is not part of the deployments category.
BACKFILL: Final[str] = """
    UPDATE session_groups sg
    SET deleted_at = (
        SELECT MAX(rg.updated_at)
        FROM replica_groups rg
        WHERE rg.session_group_id = sg.id
          AND rg.lifecycle IN ('drained', 'failed')
    )
    WHERE sg.deleted_at IS NULL
      AND EXISTS (
          SELECT 1
          FROM replica_groups rg
          WHERE rg.session_group_id = sg.id
            AND rg.lifecycle IN ('drained', 'failed')
      )
      AND NOT EXISTS (
          SELECT 1
          FROM replica_groups rg
          WHERE rg.session_group_id = sg.id
            AND rg.lifecycle NOT IN ('drained', 'failed')
      )
"""


def stamp_unserved_groups(conn: sa.Connection) -> None:
    conn.execute(sa.text(BACKFILL))


def upgrade() -> None:
    stamp_unserved_groups(op.get_bind())


def downgrade() -> None:
    # Nothing is reverted: a filled timestamp cannot be told apart from one the
    # lifecycle write stamped.
    pass
