"""add endpoint deploying_revision_id column

Record the deploy intent directly on the endpoint via a nullable
``endpoints.deploying_revision_id`` column. It points at the revision a
rollout targets and is set when a deploy is activated (transitioning the
endpoint into ``DEPLOYING`` / ``DEPLOYING_INITIALIZING``). The deploying
revision row is resolved by a direct join on this column rather than
through the replica groups.

Create Date: 2026-05-30
"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "b7d4e2a9c1f3"
down_revision = "d69322160c90"
# Part of: 26.6.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoints",
        sa.Column("deploying_revision_id", GUID(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("endpoints", "deploying_revision_id")
