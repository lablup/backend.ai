"""Assign every user their domain_member role

Reading the resource groups a domain reaches is checked at the domain scope, and no
preset held a role there that a user is given on its own. A user created before this
holds nothing at their domain.

Write the preset, give each domain the role it calls for, and assign every user the
role of the domain they belong to. A domain without a virtual entity has no scope a
role can sit in and is left out.

Revision ID: e7d2a9c41b60
Revises: f7c1b930a2d5
Create Date: 2026-09-16

"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Sequence
from typing import Any, Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7d2a9c41b60"
down_revision = "f7c1b930a2d5"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


_PRESET_ID: Final[str] = "76616aa7-6597-5b11-8629-adff5d5640c2"
_PRESET_NAME: Final[str] = "domain_member"
_SCOPE_TYPE: Final[str] = "domain"
# The bits the declaration states, one row per bit. READ on resource groups.
_GRANTS: Final[tuple[tuple[str, tuple[int, ...]], ...]] = (("resource_group", (1,)),)
_MAX_ROLE_NAME_LENGTH: Final[int] = 64
_PAGE_SIZE: Final[int] = 1000

# The seed derives an id as a uuid7 whose timestamp is fixed and whose remaining bits
# come from what it identifies, so a database migrated here and one seeded from the
# fixture hold the same rows.
_EPOCH_MS: Final[int] = 1757670718265


def _identify(*parts: str) -> str:
    digest = hashlib.blake2b("|".join(parts).encode("utf-8"), digest_size=10).digest()
    value = (_EPOCH_MS & 0xFFFFFFFFFFFF) << 80 | int.from_bytes(digest, "big")
    value &= ~(0xF << 76)
    value |= 0x7 << 76
    value &= ~(0x3 << 62)
    value |= 0x2 << 62
    return str(uuid.UUID(int=value))


def _role_ids_param(role_ids: Sequence[uuid.UUID]) -> sa.BindParameter[Any]:
    return sa.bindparam("role_ids", list(role_ids), type_=sa.ARRAY(sa.Uuid))


def _write_preset(conn: sa.engine.Connection) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO role_presets (id, name, scope_type, auto_assign, deleted)
            VALUES (CAST(:id AS uuid), :name, :scope_type, TRUE, FALSE)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                scope_type = EXCLUDED.scope_type,
                auto_assign = EXCLUDED.auto_assign,
                deleted = FALSE
        """).bindparams(id=_PRESET_ID, name=_PRESET_NAME, scope_type=_SCOPE_TYPE)
    )
    conn.execute(
        sa.text(
            "DELETE FROM role_permission_presets WHERE role_preset_id = CAST(:id AS uuid)"
        ).bindparams(id=_PRESET_ID)
    )
    rows = [
        {
            "id": _identify("role_permission_preset", _PRESET_ID, entity_type, str(bit)),
            "role_preset_id": _PRESET_ID,
            "entity_type": entity_type,
            "permission": bit,
        }
        for entity_type, bits in _GRANTS
        for bit in bits
    ]
    conn.execute(
        sa.text("""
            INSERT INTO role_permission_presets (id, role_preset_id, entity_type, permission)
            VALUES (
                CAST(:id AS uuid), CAST(:role_preset_id AS uuid), :entity_type, :permission
            )
        """),
        rows,
    )


def _create_missing_roles(conn: sa.engine.Connection) -> None:
    """Instantiate the preset in every domain that holds no role from it, the way
    creating a domain does: the role, its node, its scope's own edge and binding, and
    the preset's permissions."""
    # The name a preset without a template gives its role in a scope.
    name_prefix = _PRESET_NAME[: _MAX_ROLE_NAME_LENGTH - len("-00000000")]
    while True:
        role_ids = list(
            conn.execute(
                sa.text("""
                    INSERT INTO roles
                        (name, source, status, auto_assign, role_preset_id, scope_type, scope_id)
                    SELECT
                        :name_prefix || '-' || left(CAST(d.id AS text), 8),
                        'system', 'active', TRUE, CAST(:id AS uuid), 'domain', d.id
                    FROM domains d
                    JOIN virtual_entities node
                        ON node.entity_type = 'domain' AND node.entity_id = d.id
                    WHERE NOT EXISTS (
                        SELECT 1 FROM roles r
                        WHERE r.role_preset_id = CAST(:id AS uuid)
                          AND r.scope_type = 'domain'
                          AND r.scope_id = d.id
                    )
                    ORDER BY d.id
                    LIMIT :page_size
                    RETURNING id
                """).bindparams(name_prefix=name_prefix, id=_PRESET_ID, page_size=_PAGE_SIZE)
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
        """).bindparams(_role_ids_param(role_ids), id=_PRESET_ID)
    )


def _assign_roles(conn: sa.engine.Connection) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT u.uuid, r.id
            FROM roles r
            JOIN domains d ON d.id = r.scope_id
            JOIN users u ON u.domain_name = d.name
            WHERE r.role_preset_id = CAST(:id AS uuid)
              AND r.scope_type = 'domain'
              AND r.status = 'active'
            ON CONFLICT (user_id, role_id) DO NOTHING
        """).bindparams(id=_PRESET_ID)
    )


def mark_auto_assign(conn: sa.engine.Connection, auto_assign: bool) -> None:
    conn.execute(
        sa.text(
            "UPDATE role_presets SET auto_assign = :auto_assign WHERE id = CAST(:id AS uuid)"
        ).bindparams(auto_assign=auto_assign, id=_PRESET_ID)
    )
    conn.execute(
        sa.text(
            "UPDATE roles SET auto_assign = :auto_assign WHERE role_preset_id = CAST(:id AS uuid)"
        ).bindparams(auto_assign=auto_assign, id=_PRESET_ID)
    )


def backfill(conn: sa.engine.Connection) -> None:
    _write_preset(conn)
    _create_missing_roles(conn)
    _assign_roles(conn)


def upgrade() -> None:
    backfill(op.get_bind())


def downgrade() -> None:
    """The roles and assignments stay: taking them back takes away what users hold."""
    mark_auto_assign(op.get_bind(), False)
