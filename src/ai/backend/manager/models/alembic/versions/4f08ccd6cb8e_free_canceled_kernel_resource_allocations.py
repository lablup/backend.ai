"""free resource_allocations of CANCELLED kernels

Cleans up orphan rows in ``resource_allocations`` where the kernel is in
``CANCELLED`` state but ``free_at`` is still ``NULL``. These rows were
left behind by two factors:

1. The original backfill in ``4b7b4b040a70_add_resource_slot_normalization_tables``
   ran before ``321c033a321b_set_agent_resources_used_column_not_`` introduced
   the ``free_at`` column. Any kernel cancelled in between (or between the
   backfill and the first deployment of the runtime fix) ended up with rows
   whose ``free_at`` defaulted to ``NULL`` once the column was added.
2. Several CANCELLED-transition paths in
   ``manager.repositories.scheduler.db_source.db_source`` flip
   ``KernelRow.status`` to ``CANCELLED`` without freeing the matching
   ``ResourceAllocationRow``: ``_cancel_pending_sessions`` and
   ``cancel_kernels_by_failed_image_pull`` never touch ``free_at`` at all,
   and ``mark_session_cancelled`` updates kernels regardless of their
   current status.

A previous workaround (``BA-5060``, commit ``be8ccc830``) added a kernel
status filter to occupancy queries so the zombie rows would not inflate
``check-presets`` totals. This migration removes the underlying data
inconsistency by mirroring the runtime free behavior
(``update_kernel_status_cancelled``, ``free_kernel_resources``).

The migration marks every orphan row as freed by setting
``free_at = NOW()``. The upgrade is idempotent: re-running matches zero
rows because ``free_at`` is already set.

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
    conn = op.get_bind()

    # Mark every orphan resource_allocations row as freed.
    conn.execute(
        sa.text("""
            UPDATE resource_allocations AS ra
            SET free_at = NOW()
            FROM kernels AS k
            WHERE ra.kernel_id = k.id
              AND k.status IN ('CANCELLED', 'TERMINATED')
              AND ra.free_at IS NULL
        """)
    )


def downgrade() -> None:
    # One-way data fix: the original NULL state was the bug, and we have
    # no record of which rows were touched, so we cannot meaningfully
    # restore it. Same pattern as e.g.
    # 9dc6609c92ce_register_existing_project_roles_in_ase.
    pass
