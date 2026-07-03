"""add session scope id columns

Revision ID: ada41cb881bb
Revises: b4c5d6e7f8a9
Create Date: 2026-06-30

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ada41cb881bb"
down_revision = "b4c5d6e7f8a9"
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
    op.alter_column("sessions", "domain_id", nullable=False)
    op.alter_column("sessions", "resource_group_id", nullable=False)
    op.create_foreign_key(
        op.f("fk_sessions_domain_id_domains"),
        "sessions",
        "domains",
        ["domain_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_sessions_resource_group_id_scaling_groups"),
        "sessions",
        "scaling_groups",
        ["resource_group_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_sessions_resource_group_id_scaling_groups"),
        "sessions",
        type_="foreignkey",
    )
    op.drop_constraint(op.f("fk_sessions_domain_id_domains"), "sessions", type_="foreignkey")
    op.drop_index("ix_sessions_resource_group_id", table_name="sessions")
    op.drop_index("ix_sessions_domain_id", table_name="sessions")
    op.drop_column("sessions", "resource_group_id")
    op.drop_column("sessions", "domain_id")
