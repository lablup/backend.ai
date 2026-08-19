"""add reserved_at column to resource_allocations

Adds a ``reserved_at`` timestamp so an allocation row carries its own
lifecycle: created (enqueue) -> reserved (hold established at SCHEDULED,
or at RESERVED for a preemption reservation) -> used (running) -> free.

Backfills ``reserved_at`` for rows whose hold is already established
(active rows of kernels past PENDING) using the row's creation time as
the best available approximation.

Create Date: 2026-07-27

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cd6332715576"
down_revision = "c4e1a7f9b26d"
# Part of: 26.8.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resource_allocations",
        sa.Column(
            "reserved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Backfill: active allocations of kernels already past PENDING hold a
    # reservation today; stamp them with the row's creation time.
    op.execute("""
        UPDATE resource_allocations ra
        SET reserved_at = ra.created_at
        FROM kernels k
        WHERE k.id = ra.kernel_id
          AND ra.reserved_at IS NULL
          AND ra.free_at IS NULL
          AND k.status NOT IN ('PENDING', 'CANCELLED')
    """)


def downgrade() -> None:
    op.drop_column("resource_allocations", "reserved_at")
