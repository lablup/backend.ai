"""add login_client_type_id to login_sessions

Revision ID: c7f2a8e31b04
Revises: b4e7f1a2c3d5
Create Date: 2026-04-14

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c7f2a8e31b04"
down_revision = "b4e7f1a2c3d5"
# Part of: 26.3.0
branch_labels = None
depends_on = None

_SEED_CORE_ID = uuid.UUID("00000000-0000-0000-0000-00000000c02e")
_SEED_WEBUI_ID = uuid.UUID("00000000-0000-0000-0000-0000000000eb")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Ensure login_client_types table exists (may have been skipped in be1ac9308056).
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
            ],
        )

    # Add login_client_type_id FK column to login_sessions.
    existing_columns = [c["name"] for c in inspector.get_columns("login_sessions")]
    if "login_client_type_id" not in existing_columns:
        op.add_column(
            "login_sessions",
            sa.Column(
                "login_client_type_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )
        op.create_foreign_key(
            "fk_login_sessions_login_client_type_id",
            "login_sessions",
            "login_client_types",
            ["login_client_type_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            "ix_login_sessions_login_client_type_id",
            "login_sessions",
            ["login_client_type_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = [c["name"] for c in inspector.get_columns("login_sessions")]
    if "login_client_type_id" in existing_columns:
        op.drop_index("ix_login_sessions_login_client_type_id", table_name="login_sessions")
        op.drop_constraint(
            "fk_login_sessions_login_client_type_id", "login_sessions", type_="foreignkey"
        )
        op.drop_column("login_sessions", "login_client_type_id")
