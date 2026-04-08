"""add login_client_types table and FK on login_sessions

Revision ID: e6036371b6b5
Revises: 6e104991787d
Create Date: 2026-04-08

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e6036371b6b5"
down_revision = "6e104991787d"
# Part of: 26.3.0
branch_labels = None
depends_on = None


# Fixed UUIDs for seed rows so references (tests, GQL selections) stay stable.
_SEED_CORE_ID = uuid.UUID("00000000-0000-0000-0000-00000000c02e")
_SEED_WEBUI_ID = uuid.UUID("00000000-0000-0000-0000-0000000000eb")
_SEED_FASTTRACK_ID = uuid.UUID("00000000-0000-0000-0000-00000000fa57")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # --- Create login_client_types table -----------------------------------------------
    if "login_client_types" not in inspector.get_table_names():
        op.create_table(
            "login_client_types",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("uuid_generate_v4()"),
            ),
            sa.Column("name", sa.String(length=64), nullable=False, unique=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "modified_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                nullable=False,
            ),
        )

        # Seed the three well-known client types so existing login flows keep working
        # right after the migration. Administrators can add/remove types afterwards
        # via the login_client_type CRUD APIs.
        login_client_types_table = sa.table(
            "login_client_types",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("name", sa.String),
            sa.column("description", sa.Text),
        )
        op.bulk_insert(
            login_client_types_table,
            [
                {
                    "id": _SEED_CORE_ID,
                    "name": "core",
                    "description": "Backend.AI CLI / core SDK clients.",
                },
                {
                    "id": _SEED_WEBUI_ID,
                    "name": "webui",
                    "description": "Backend.AI web console.",
                },
                {
                    "id": _SEED_FASTTRACK_ID,
                    "name": "fasttrack",
                    "description": "Backend.AI FastTrack workflow client.",
                },
            ],
        )

    # --- Clean up the interim enum column, add FK column --------------------------------
    login_session_cols = {c["name"] for c in inspector.get_columns("login_sessions")}
    if "client_type" in login_session_cols:
        interim_indexes = {idx["name"] for idx in inspector.get_indexes("login_sessions")}
        if "ix_login_sessions_user_id_client_type_status" in interim_indexes:
            op.drop_index(
                "ix_login_sessions_user_id_client_type_status",
                table_name="login_sessions",
            )
        op.drop_column("login_sessions", "client_type")
        login_session_cols = {c["name"] for c in sa.inspect(bind).get_columns("login_sessions")}

    if "login_client_type_id" not in login_session_cols:
        op.add_column(
            "login_sessions",
            sa.Column(
                "login_client_type_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("login_client_types.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    existing_indexes = {idx["name"] for idx in sa.inspect(bind).get_indexes("login_sessions")}
    if "ix_login_sessions_user_id_login_client_type_id_status" not in existing_indexes:
        op.create_index(
            "ix_login_sessions_user_id_login_client_type_id_status",
            "login_sessions",
            ["user_id", "login_client_type_id", "status"],
        )

    # New composite index covers (user_id, status) lookups via prefix match, so the old
    # 2-column index is redundant.
    if "ix_login_sessions_user_id_status" in existing_indexes:
        op.drop_index("ix_login_sessions_user_id_status", table_name="login_sessions")


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
    if "ix_login_sessions_user_id_login_client_type_id_status" in existing_indexes:
        op.drop_index(
            "ix_login_sessions_user_id_login_client_type_id_status",
            table_name="login_sessions",
        )

    login_session_cols = {c["name"] for c in inspector.get_columns("login_sessions")}
    if "login_client_type_id" in login_session_cols:
        op.drop_column("login_sessions", "login_client_type_id")

    if "login_client_types" in inspector.get_table_names():
        op.drop_table("login_client_types")
