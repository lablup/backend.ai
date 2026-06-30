"""add session scope id columns

Revision ID: ada41cb881bb
Revises: e3b8d2a1c5f7
Create Date: 2026-06-30

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ada41cb881bb"
down_revision = "e3b8d2a1c5f7"
# Part of: 26.7.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("domain_id", GUID(), nullable=True))
    op.add_column("sessions", sa.Column("resource_group_id", GUID(), nullable=True))
    op.create_index("ix_sessions_domain_id", "sessions", ["domain_id"])
    op.create_index("ix_sessions_resource_group_id", "sessions", ["resource_group_id"])

    op.execute(
        sa.text("""
        UPDATE sessions
        SET domain_id = domains.id
        FROM domains
        WHERE sessions.domain_name = domains.name
          AND sessions.domain_id IS NULL
        """)
    )
    op.execute(
        sa.text("""
        UPDATE sessions
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE sessions.scaling_group_name = scaling_groups.name
          AND sessions.resource_group_id IS NULL
        """)
    )


def downgrade() -> None:
    op.drop_index("ix_sessions_resource_group_id", table_name="sessions")
    op.drop_index("ix_sessions_domain_id", table_name="sessions")
    op.drop_column("sessions", "resource_group_id")
    op.drop_column("sessions", "domain_id")
