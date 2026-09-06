"""add id column to session dependencies

Revision ID: 8c41a7e5b6d2
Revises: 96014c885c33
Create Date: 2026-08-24 23:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "8c41a7e5b6d2"
down_revision = "96014c885c33"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "session_dependencies",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_session_dependencies_id", "session_dependencies", ["id"])


def downgrade() -> None:
    op.drop_constraint("uq_session_dependencies_id", "session_dependencies", type_="unique")
    op.drop_column("session_dependencies", "id")
