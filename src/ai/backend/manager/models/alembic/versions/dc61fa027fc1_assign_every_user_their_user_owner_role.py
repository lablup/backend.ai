"""Assign every user their user_owner role

The user_owner preset is now assigned on its own, so a user created from here on holds
the role of their own scope. A user created before holds nothing from it.

Mark the preset and the roles instantiated from it as assigned on their own, give each
user without such a role one, and assign every user theirs. A user without a virtual
entity has no scope a role can sit in and is left out.

Revision ID: dc61fa027fc1
Revises: f4a1c9d20b73
Create Date: 2026-09-15

"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dc61fa027fc1"
down_revision = "f4a1c9d20b73"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


_USER_OWNER_PRESET_ID: Final[str] = "776c1366-dcf3-5abd-b8de-bc3ad3b759ad"
_MAX_ROLE_NAME_LENGTH: Final[int] = 64
_PAGE_SIZE: Final[int] = 1000


def _role_ids_param(role_ids: Sequence[uuid.UUID]) -> sa.BindParameter[Any]:
    return sa.bindparam("role_ids", list(role_ids), type_=sa.ARRAY(sa.Uuid))


def _mark_auto_assign(conn: sa.engine.Connection, auto_assign: bool) -> None:
    conn.execute(
        sa.text(
            "UPDATE role_presets SET auto_assign = :auto_assign WHERE id = CAST(:id AS uuid)"
        ).bindparams(auto_assign=auto_assign, id=_USER_OWNER_PRESET_ID)
    )
    conn.execute(
        sa.text(
            "UPDATE roles SET auto_assign = :auto_assign WHERE role_preset_id = CAST(:id AS uuid)"
        ).bindparams(auto_assign=auto_assign, id=_USER_OWNER_PRESET_ID)
    )


def _create_missing_roles(conn: sa.engine.Connection) -> None:
    """Instantiate the preset in every user scope that holds no role from it, the way
    creating a user does: the role, its node, its scope's own edge and binding, and the
    preset's permissions."""
    preset_name = conn.execute(
        sa.text(
            "SELECT name FROM role_presets WHERE id = CAST(:id AS uuid) AND deleted IS FALSE"
        ).bindparams(id=_USER_OWNER_PRESET_ID)
    ).scalar()
    if preset_name is None:
        return
    # The name a preset without a template gives its role in a scope.
    name_prefix = str(preset_name)[: _MAX_ROLE_NAME_LENGTH - len("-00000000")]
    while True:
        role_ids = list(
            conn.execute(
                sa.text("""
                    INSERT INTO roles
                        (name, source, status, auto_assign, role_preset_id, scope_type, scope_id)
                    SELECT
                        :name_prefix || '-' || left(CAST(u.uuid AS text), 8),
                        'system', 'active', TRUE, CAST(:id AS uuid), 'user', u.uuid
                    FROM users u
                    JOIN virtual_entities node
                        ON node.entity_type = 'user' AND node.entity_id = u.uuid
                    WHERE NOT EXISTS (
                        SELECT 1 FROM roles r
                        WHERE r.role_preset_id = CAST(:id AS uuid)
                          AND r.scope_type = 'user'
                          AND r.scope_id = u.uuid
                    )
                    ORDER BY u.uuid
                    LIMIT :page_size
                    RETURNING id
                """).bindparams(
                    name_prefix=name_prefix, id=_USER_OWNER_PRESET_ID, page_size=_PAGE_SIZE
                )
            ).scalars()
        )
        if not role_ids:
            return
        _put_in_graph(conn, role_ids)
        _grant_preset_permissions(conn, role_ids)


def _put_in_graph(conn: sa.engine.Connection, role_ids: Sequence[uuid.UUID]) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO virtual_entities (entity_type, entity_id)
            SELECT 'role', role_id FROM unnest(:role_ids) AS role_id
            ON CONFLICT (entity_type, entity_id) DO NOTHING
        """).bindparams(_role_ids_param(role_ids))
    )
    conn.execute(
        sa.text("""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT node.id, node.id, FALSE
            FROM virtual_entities node
            WHERE node.entity_type = 'role' AND node.entity_id = ANY(:role_ids)
            UNION ALL
            SELECT scope.id, node.id, FALSE
            FROM roles r
            JOIN virtual_entities node ON node.entity_type = 'role' AND node.entity_id = r.id
            JOIN virtual_entities scope
                ON scope.entity_type = r.scope_type AND scope.entity_id = r.scope_id
            WHERE r.id = ANY(:role_ids)
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """).bindparams(_role_ids_param(role_ids))
    )
    conn.execute(
        sa.text("""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT node.id, node.id, CAST(NULL AS smallint)
            FROM virtual_entities node
            WHERE node.entity_type = 'role' AND node.entity_id = ANY(:role_ids)
            UNION ALL
            SELECT node.id, scope.id, CAST(NULL AS smallint)
            FROM roles r
            JOIN virtual_entities node ON node.entity_type = 'role' AND node.entity_id = r.id
            JOIN virtual_entities scope
                ON scope.entity_type = r.scope_type AND scope.entity_id = r.scope_id
            WHERE r.id = ANY(:role_ids)
            ON CONFLICT DO NOTHING
        """).bindparams(_role_ids_param(role_ids))
    )


def _grant_preset_permissions(conn: sa.engine.Connection, role_ids: Sequence[uuid.UUID]) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO permissions (role_id, entity_type, permission)
            SELECT role_id, p.entity_type, p.permission
            FROM unnest(:role_ids) AS role_id
            CROSS JOIN role_permission_presets p
            WHERE p.role_preset_id = CAST(:id AS uuid) AND p.permission <> 0
        """).bindparams(_role_ids_param(role_ids), id=_USER_OWNER_PRESET_ID)
    )


def _assign_roles(conn: sa.engine.Connection) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.uuid, r.id
            FROM roles r
            JOIN users u ON u.uuid = r.scope_id
            WHERE r.role_preset_id = CAST(:id AS uuid)
              AND r.scope_type = 'user'
              AND r.status = 'active'
            ON CONFLICT (user_id, role_id) DO NOTHING
        """).bindparams(id=_USER_OWNER_PRESET_ID)
    )


def backfill(conn: sa.engine.Connection) -> None:
    _mark_auto_assign(conn, True)
    _create_missing_roles(conn)
    _assign_roles(conn)


def upgrade() -> None:
    backfill(op.get_bind())


def downgrade() -> None:
    """The roles and assignments stay: taking them back takes away what users hold."""
    _mark_auto_assign(op.get_bind(), False)
