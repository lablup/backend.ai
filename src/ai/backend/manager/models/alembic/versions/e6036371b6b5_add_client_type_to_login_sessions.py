"""add client_type to login_sessions

Revision ID: e6036371b6b5
Revises: 689f66507280
Create Date: 2026-04-06

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e6036371b6b5"
down_revision = "689f66507280"
# Part of: 26.3.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("login_sessions")}
    if "client_type" not in cols:
        op.add_column(
            "login_sessions",
            sa.Column(
                "client_type",
                sa.String(length=64),
                nullable=False,
                server_default="default",
            ),
        )
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("login_sessions")}
    if "ix_login_sessions_user_id_client_type_status" not in existing_indexes:
        op.create_index(
            "ix_login_sessions_user_id_client_type_status",
            "login_sessions",
            ["user_id", "client_type", "status"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("login_sessions")}
    if "ix_login_sessions_user_id_client_type_status" in existing_indexes:
        op.drop_index(
            "ix_login_sessions_user_id_client_type_status",
            table_name="login_sessions",
        )
    cols = {c["name"] for c in inspector.get_columns("login_sessions")}
    if "client_type" in cols:
        op.drop_column("login_sessions", "client_type")
