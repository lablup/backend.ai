"""create login_session tables

Revision ID: 19e48e70b86a
Revises: 3b6297b1bd75
Create Date: 2026-03-25 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

revision = "19e48e70b86a"
down_revision = "3b6297b1bd75"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "login_sessions",
        sa.Column("id", GUID, server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("session_token", sa.String(64), nullable=False),
        sa.Column("user_id", GUID, nullable=False),
        sa.Column("access_key", sa.String(20), nullable=False),
        sa.Column("status", sa.VARCHAR(64), nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_login_sessions")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name=op.f("fk_login_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("session_token", name=op.f("uq_login_sessions_session_token")),
    )
    op.create_index(
        op.f("ix_login_sessions_session_token"), "login_sessions", ["session_token"], unique=True
    )
    op.create_index(op.f("ix_login_sessions_user_id"), "login_sessions", ["user_id"])
    op.create_index(op.f("ix_login_sessions_status"), "login_sessions", ["status"])
    op.create_index(op.f("ix_login_sessions_expires_at"), "login_sessions", ["expires_at"])
    op.create_index("ix_login_sessions_user_id_status", "login_sessions", ["user_id", "status"])

    op.create_table(
        "login_history",
        sa.Column("id", GUID, server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", GUID, nullable=False),
        sa.Column("domain_name", sa.String(64), nullable=False),
        sa.Column("result", sa.VARCHAR(64), nullable=False),
        sa.Column("fail_reason", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_login_history")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.uuid"],
            name=op.f("fk_login_history_user_id_users"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(op.f("ix_login_history_user_id"), "login_history", ["user_id"])
    op.create_index(op.f("ix_login_history_result"), "login_history", ["result"])
    op.create_index(op.f("ix_login_history_created_at"), "login_history", ["created_at"])
    op.create_index(
        "ix_login_history_user_id_created_at", "login_history", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("login_history")
    op.drop_table("login_sessions")
