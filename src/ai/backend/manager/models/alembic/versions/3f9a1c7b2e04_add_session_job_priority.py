"""add-session-job-priority

Revision ID: 3f9a1c7b2e04
Revises: 4a39641d0fc2
Create Date: 2026-07-19 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.common.defs.session import JOB_PRIORITY_DEFAULT

# revision identifiers, used by Alembic.
revision = "3f9a1c7b2e04"
down_revision = "4a39641d0fc2"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column(
            "job_priority",
            sa.Integer(),
            nullable=False,
            server_default=sa.text(str(JOB_PRIORITY_DEFAULT)),
        ),
    )


def downgrade() -> None:
    op.drop_column("sessions", "job_priority")
