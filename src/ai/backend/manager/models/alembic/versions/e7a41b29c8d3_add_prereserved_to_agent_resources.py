"""add prereserved columns for advance reservations

Separates advance reservations (holds granted while a preemption plan
waits for its victims to free resources) from the admitted holds in
``reserved``: ``used + reserved <= capacity`` stays the admission
invariant, while ``reserved + prereserved <= capacity`` bounds the total
future holds. A reservation moves from ``prereserved`` into ``reserved``
once ``used + reserved`` plus its own amount fits the capacity.

``resource_allocations`` mirrors the buckets per row: ``prereserved`` and
``reserved`` record where the row's hold currently sits (``requested``
stays the user's ask and never feeds the aggregates), and
``prereserved_at`` / ``reserved_at`` record when each hold was made (the
former is the release ordering key). Freeing a row subtracts the row's
bucket values from the agent counters unconditionally.

Create Date: 2026-07-27

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7a41b29c8d3"
down_revision = "cd6332715576"
# Part of: 26.8.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_resources",
        sa.Column(
            "prereserved",
            sa.Numeric(precision=24, scale=6),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "resource_allocations",
        sa.Column(
            "prereserved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "resource_allocations",
        sa.Column(
            "prereserved",
            sa.Numeric(precision=24, scale=6),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "resource_allocations",
        sa.Column(
            "reserved",
            sa.Numeric(precision=24, scale=6),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    # Backfill: kernels between SCHEDULED and RUNNING hold their amount in
    # ``reserved`` (running rows' holds already moved into ``used``).
    op.execute("""
        UPDATE resource_allocations ra
        SET reserved = ra.requested
        FROM kernels k
        WHERE k.id = ra.kernel_id
          AND ra.free_at IS NULL
          AND ra.used_at IS NULL
          AND k.status IN ('SCHEDULED', 'PREPARING', 'PULLING', 'PREPARED', 'CREATING')
    """)


def downgrade() -> None:
    op.drop_column("resource_allocations", "reserved")
    op.drop_column("resource_allocations", "prereserved")
    op.drop_column("resource_allocations", "prereserved_at")
    op.drop_column("agent_resources", "prereserved")
