"""Name the agent by uuid on agent_resources

The v2 field write builds a row under its owner's entity id, which for an agent is
``agents.uuid``. The row named the agent by ``agents.id`` alone, so the id is added
beside it; the key and every existing query keep using the name.

No foreign key: ``agent_id`` already carries one to the same table, and a second
would leave every join between the two tables ambiguous.

Create Date: 2026-09-09

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c7d419b0a58e"
down_revision = "c8d5b2740f1e"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_resources", sa.Column("agent_uuid", GUID(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE agent_resources SET agent_uuid = agents.uuid "
            "FROM agents WHERE agent_resources.agent_id = agents.id"
        )
    )
    # A row whose agent is already gone cannot be pointed at one.
    op.execute(sa.text("DELETE FROM agent_resources WHERE agent_uuid IS NULL"))
    op.alter_column("agent_resources", "agent_uuid", nullable=False)


def downgrade() -> None:
    op.drop_column("agent_resources", "agent_uuid")
