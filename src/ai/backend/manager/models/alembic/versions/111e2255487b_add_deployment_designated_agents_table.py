"""add deployment_designated_agents table

Records which agents a deployment designates for its route sessions.

Revision ID: 111e2255487b
Revises: a31e8d4c9b72
Create Date: 2026-10-19 17:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "111e2255487b"
down_revision = "a31e8d4c9b72"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deployment_designated_agents",
        sa.Column("endpoint_id", GUID(), nullable=False),
        sa.Column("agent_uuid", GUID(), nullable=False),
        sa.PrimaryKeyConstraint(
            "endpoint_id", "agent_uuid", name=op.f("pk_deployment_designated_agents")
        ),
        sa.ForeignKeyConstraint(
            ["endpoint_id"],
            ["endpoints.id"],
            name=op.f("fk_deployment_designated_agents_endpoint_id_endpoints"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_uuid"],
            ["agents.uuid"],
            name=op.f("fk_deployment_designated_agents_agent_uuid_agents"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_deployment_designated_agents_agent_uuid"),
        "deployment_designated_agents",
        ["agent_uuid"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_deployment_designated_agents_agent_uuid"),
        table_name="deployment_designated_agents",
    )
    op.drop_table("deployment_designated_agents")
