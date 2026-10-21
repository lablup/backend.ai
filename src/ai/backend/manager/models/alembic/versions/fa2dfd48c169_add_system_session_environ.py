"""Add system_session_environ

Create the table deciding which values the manager injects into a session's
environment, and bind every value source at the global scope under the name the
launcher has always used. The session owner's values are bound disabled.

Revision ID: fa2dfd48c169
Revises: e234d84a162f
Create Date: 2026-10-14

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "fa2dfd48c169"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e234d84a162f"
branch_labels = None
depends_on = None

# value_source to key, bound enabled.
REQUIRED_BINDINGS: Final[dict[str, str]] = {
    "session_id": "BACKENDAI_SESSION_ID",
    "session_name": "BACKENDAI_SESSION_NAME",
    "cluster_size": "BACKENDAI_CLUSTER_SIZE",
    "cluster_replicas": "BACKENDAI_CLUSTER_REPLICAS",
    "cluster_hosts": "BACKENDAI_CLUSTER_HOSTS",
    "preopen_ports": "BACKENDAI_PREOPEN_PORTS",
}

# value_source to key, bound disabled.
OPTIONAL_BINDINGS: Final[dict[str, str]] = {
    "user_uuid": "BACKENDAI_USER_UUID",
    "user_email": "BACKENDAI_USER_EMAIL",
    "user_name": "BACKENDAI_USER_NAME",
    "access_key": "BACKENDAI_ACCESS_KEY",
}

_ADD_GLOBAL_BINDING: Final = sa.text("""
    INSERT INTO system_session_environ (value_source, key, scope_type, scope_id, disabled)
    VALUES (:value_source, :key, 'global', NULL, :disabled)
    ON CONFLICT (key, scope_type, scope_id) DO NOTHING
""")


def upgrade() -> None:
    op.create_table(
        "system_session_environ",
        sa.Column("id", GUID, server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("value_source", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=256), nullable=False),
        sa.Column("scope_type", sa.String(length=64), nullable=False),
        sa.Column("scope_id", GUID, nullable=True),
        sa.Column("disabled", sa.Boolean, server_default=sa.false(), nullable=False),
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
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint(
            "(scope_type = 'global') = (scope_id IS NULL)",
            name=op.f("ck_system_session_environ_scope_id_matches_scope_type"),
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
    for value_source, key in REQUIRED_BINDINGS.items():
        conn.execute(
            _ADD_GLOBAL_BINDING, {"value_source": value_source, "key": key, "disabled": False}
        )
    for value_source, key in OPTIONAL_BINDINGS.items():
        conn.execute(
            _ADD_GLOBAL_BINDING, {"value_source": value_source, "key": key, "disabled": True}
        )


def downgrade() -> None:
    op.drop_index("ix_system_session_environ_scope", table_name="system_session_environ")
    op.drop_table("system_session_environ")
