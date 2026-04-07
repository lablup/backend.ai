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
                # Pre-existing sessions are assumed to be webui logins, matching
                # the AuthorizeRequest default for callers that omit client_type.
                server_default="webui",
            ),
        )
    else:
        # Previous iterations of this migration used "default" or "core" as the
        # placeholder. Collapse any such rows onto "webui" to match the
        # AuthorizeRequest default, and update the column default accordingly.
        op.execute(
            sa.text(
                "UPDATE login_sessions SET client_type = 'webui' "
                "WHERE client_type IN ('default', 'core')"
            )
        )
        op.alter_column("login_sessions", "client_type", server_default="webui")
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("login_sessions")}
    if "ix_login_sessions_user_id_client_type_status" not in existing_indexes:
        op.create_index(
            "ix_login_sessions_user_id_client_type_status",
            "login_sessions",
            ["user_id", "client_type", "status"],
        )
    # The new composite index covers (user_id, status) lookups via prefix match,
    # so the old 2-column index is redundant.
    if "ix_login_sessions_user_id_status" in existing_indexes:
        op.drop_index(
            "ix_login_sessions_user_id_status",
            table_name="login_sessions",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("login_sessions")}
    if "ix_login_sessions_user_id_status" not in existing_indexes:
        op.create_index(
            "ix_login_sessions_user_id_status",
            "login_sessions",
            ["user_id", "status"],
        )
    if "ix_login_sessions_user_id_client_type_status" in existing_indexes:
        op.drop_index(
            "ix_login_sessions_user_id_client_type_status",
            table_name="login_sessions",
        )
    cols = {c["name"] for c in inspector.get_columns("login_sessions")}
    if "client_type" in cols:
        op.drop_column("login_sessions", "client_type")
