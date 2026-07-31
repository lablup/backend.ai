"""create session_idle_checks

Store each session's projected cleanup time and latest judgment per applied
idle checker (BEP-1054).

Revision ID: 5c92586bff94
Revises: b3f1a9c2d7e4
Create Date: 2026-07-16

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "5c92586bff94"
down_revision = "b3f1a9c2d7e4"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "session_idle_checks",
        sa.Column("session_id", GUID, nullable=False),
        sa.Column("idle_checker_id", GUID, nullable=False),
        sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=64), nullable=False),
        sa.Column("last_message", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name="fk_session_idle_checks_session_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["idle_checker_id"],
            ["idle_checkers.id"],
            name="fk_session_idle_checks_idle_checker_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "session_id",
            "idle_checker_id",
            name="pk_session_idle_checks",
        ),
    )
    op.create_index(
        "ix_session_idle_checks_expire_at_not_null",
        "session_idle_checks",
        ["expire_at"],
        postgresql_where=sa.text("expire_at IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_session_idle_checks_expire_at_not_null",
        table_name="session_idle_checks",
    )
    op.drop_table("session_idle_checks")
