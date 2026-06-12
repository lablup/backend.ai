"""add route termination grace period

Adds a termination grace period so a route's session stays alive for a
configurable time after its traffic is drained from AppProxy, letting
in-flight requests finish before the kernel is killed.

- ``deployment_revisions.termination_grace_period``: per-revision setting.
- ``routings.termination_grace_period``: copied from the revision at route
  creation.

Also backfills ``sub_status`` for routes already TERMINATING so they enter
the new two-stage pipeline (DRAINING → COOLING_DOWN) at its first stage.

Revision ID: b7fa28e23b29
Revises: f3a8c1d05e64
Create Date: 2026-06-12

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7fa28e23b29"
down_revision = "f3a8c1d05e64"
# Part of: {NEXT_RELEASE_VERSION}
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deployment_revisions",
        sa.Column(
            "termination_grace_period",
            sa.Float(),
            nullable=False,
            server_default="30",
        ),
    )
    op.add_column(
        "routings",
        sa.Column(
            "termination_grace_period",
            sa.Float(),
            nullable=False,
            server_default="30",
        ),
    )
    op.execute(
        "UPDATE routings SET sub_status = 'draining' WHERE status = 'terminating'",
    )


def downgrade() -> None:
    # Older code cannot parse the terminating-stage sub_status values.
    op.execute(
        "UPDATE routings SET sub_status = NULL WHERE sub_status IN ('draining', 'cooling_down')",
    )
    op.drop_column("routings", "termination_grace_period")
    op.drop_column("deployment_revisions", "termination_grace_period")
