"""add prereserved column to agent_resources

Separates advance reservations (holds granted while a preemption plan
waits for its victims to free resources) from the admitted holds in
``reserved``: ``used + reserved <= capacity`` stays the admission
invariant, while ``reserved + prereserved <= capacity`` bounds the total
future holds. A reservation moves from ``prereserved`` into ``reserved``
once ``used + reserved`` plus its own amount fits the capacity.

Create Date: 2026-07-27

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7a41b29c8d3"
down_revision = "cd6332715576"
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


def downgrade() -> None:
    op.drop_column("agent_resources", "prereserved")
