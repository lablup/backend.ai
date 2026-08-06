"""add uuid column to agents table

Revision ID: 13f4b8bc37f2
Revises: c1a7d3f05e28
Create Date: 2026-08-06 01:43:22.390606

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "13f4b8bc37f2"
down_revision = "c1a7d3f05e28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "uuid",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_agents_uuid", "agents", ["uuid"])


def downgrade() -> None:
    op.drop_constraint("uq_agents_uuid", "agents", type_="unique")
    op.drop_column("agents", "uuid")
