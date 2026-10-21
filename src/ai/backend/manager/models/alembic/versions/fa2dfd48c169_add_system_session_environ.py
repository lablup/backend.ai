"""Add system_session_environ

Create the table deciding which values the manager injects into a session's
environment, and bind every value source at the global scope under the name the
launcher has always used. The session owner's values are bound disabled.

Revision ID: fa2dfd48c169
Revises: e234d84a162f
Create Date: 2026-10-14

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.system_session_environ.seed import SEED_SYSTEM_SESSION_ENVIRON_SQL

# revision identifiers, used by Alembic.
revision = "fa2dfd48c169"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e234d84a162f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_session_environ",
        sa.Column("id", GUID, server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("value_source", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=256), nullable=False),
        sa.Column("scope_type", sa.String(length=64), nullable=False),
        sa.Column("scope_id", GUID, nullable=False),
        sa.Column("enabled", sa.Boolean, server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_system_session_environ")),
        sa.UniqueConstraint(
            "key",
            "scope_type",
            "scope_id",
            name=op.f("uq_system_session_environ_key"),
        ),
        sa.CheckConstraint(
            "key ~ '^[A-Za-z_][A-Za-z0-9_]*$'",
            name=op.f("ck_system_session_environ_key_is_environ_name"),
        ),
    )
    op.create_index(
        "ix_system_session_environ_scope",
        "system_session_environ",
        ["scope_type", "scope_id"],
    )
    conn = op.get_bind()
    for statement in SEED_SYSTEM_SESSION_ENVIRON_SQL:
        conn.execute(sa.text(statement))


def downgrade() -> None:
    op.drop_index("ix_system_session_environ_scope", table_name="system_session_environ")
    op.drop_table("system_session_environ")
