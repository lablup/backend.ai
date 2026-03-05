"""Add login_sessions table and login_security_policy column to users

Revision ID: ba49050abc12
Revises: ffcf0ed13a26
Create Date: 2026-03-06 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "ba49050abc12"
down_revision = "ffcf0ed13a26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "login_sessions",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("user_uuid", GUID(), nullable=False),
        sa.Column("session_token", sa.String(length=512), nullable=False),
        sa.Column("client_ip", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_uuid"],
            ["users.uuid"],
            name=op.f("fk_login_sessions_user_uuid_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_login_sessions")),
        sa.UniqueConstraint("session_token", name=op.f("uq_login_sessions_session_token")),
    )
    op.create_index(
        op.f("ix_login_sessions_user_uuid"),
        "login_sessions",
        ["user_uuid"],
        unique=False,
    )
    op.add_column(
        "users",
        sa.Column(
            "login_security_policy",
            sa.dialects.postgresql.JSONB(none_as_null=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "login_security_policy")
    op.drop_index(op.f("ix_login_sessions_user_uuid"), table_name="login_sessions")
    op.drop_table("login_sessions")
