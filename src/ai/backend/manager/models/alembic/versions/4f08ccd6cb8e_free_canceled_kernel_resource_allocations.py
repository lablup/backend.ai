"""free resource_allocations of CANCELLED kernels

Cleans up orphan rows in ``resource_allocations`` where the kernel is in
``CANCELLED`` state but ``free_at`` is still ``NULL``. These rows were
left behind by two factors:

1. The original backfill in ``4b7b4b040a70_add_resource_slot_normalization_tables``
   ran before ``321c033a321b_set_agent_resources_used_column_not_`` introduced
   the ``free_at`` column. Any kernel cancelled in between (or between the
   backfill and the first deployment of the runtime fix) ended up with rows
   whose ``free_at`` defaulted to ``NULL`` once the column was added.
2. The batch cancel path ``_cancel_pending_sessions`` in
   ``manager.repositories.scheduler.db_source.db_source`` flips
   ``KernelRow.status`` to ``CANCELLED`` without touching
   ``ResourceAllocationRow.free_at``, so it kept producing zombies even
   after the runtime fix shipped.

A previous workaround (``BA-5060``, commit ``be8ccc830``) added a kernel
status filter to occupancy queries so the zombie rows would not inflate
``check-presets`` totals. This migration removes the underlying data
inconsistency by marking those rows as freed, matching the behaviour of
``update_kernel_status_cancelled`` and ``free_kernel_resources``.

A ``CANCELLED`` kernel can only have transitioned from
``PENDING/SCHEDULED/PREPARING/PULLING/CREATING``, so
``ResourceAllocationRow.used`` is always ``NULL`` for these rows and no
``agent_resources.used`` adjustment is required.

Revision ID: 4f08ccd6cb8e
Revises: 99805291b6e0
Create Date: 2026-04-08

"""

# Part of: 26.3.0 (main)

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4f08ccd6cb8e"
down_revision = "99805291b6e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text("""
            UPDATE resource_allocations AS ra
            SET free_at = NOW()
            FROM kernels AS k
            WHERE ra.kernel_id = k.id
              AND k.status = 'CANCELLED'
              AND ra.free_at IS NULL
        """)
    )


def downgrade() -> None:
    pass
