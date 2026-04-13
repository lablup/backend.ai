"""add login_client_types table

Revision ID: be1ac9308056
Revises: 2c9000848b6e
Create Date: 2026-04-09

"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "be1ac9308056"
down_revision = "2c9000848b6e"
# Part of: 26.3.0
branch_labels = None
depends_on = None

# Fixed UUIDs for seed rows so references stay stable.
_SEED_CORE_ID = uuid.UUID("00000000-0000-0000-0000-00000000c02e")
_SEED_WEBUI_ID = uuid.UUID("00000000-0000-0000-0000-0000000000eb")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

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


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "login_client_types" in inspector.get_table_names():
        op.drop_table("login_client_types")
