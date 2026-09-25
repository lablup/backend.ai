"""Add the preset scope and the public_member role

A preset names the one scope its role is created in with `role_presets.scope_id`; NULL
keeps creating the role in every scope of its type.

Write the public_member preset for the public global entity and create its role there.
Granting the role to users is left to a later revision.

Revision ID: c3e8a1f05b27
Revises: b76f2d5191d4
Create Date: 2026-09-18

"""

from __future__ import annotations

import hashlib
import uuid
from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c3e8a1f05b27"  # Part of: NEXT_RELEASE_VERSION
down_revision = "b76f2d5191d4"
branch_labels = None
depends_on = None


_PRESET_ID: Final[str] = "01993d56-bb39-7d13-a84b-b6a84fc8b7fd"
_PRESET_NAME: Final[str] = "public_member"
_SCOPE_TYPE: Final[str] = "global"
_SCOPE_NAME: Final[str] = "public"
# The bits the declaration states, one row per bit. READ on each type.
_GRANTS: Final[tuple[tuple[str, tuple[int, ...]], ...]] = (
    ("app_config_fragment", (1,)),
    ("container_registry", (1,)),
    ("deployment_preset", (1,)),
    ("image", (1,)),
    ("login_client_type", (1,)),
    ("prometheus_query_preset", (1,)),
    ("prometheus_query_preset_category", (1,)),
    ("resource_preset", (1,)),
    ("resource_slot_type", (1,)),
    ("runtime_variant", (1,)),
    ("runtime_variant_preset", (1,)),
)
_MAX_ROLE_NAME_LENGTH: Final[int] = 64

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


def _write_preset(conn: sa.engine.Connection) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO role_presets (id, name, scope_type, scope_id, auto_assign, deleted)
            SELECT CAST(:id AS uuid), :name, :scope_type, g.id, TRUE, FALSE
            FROM global_entities g
            WHERE g.name = :scope_name
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                scope_type = EXCLUDED.scope_type,
                scope_id = EXCLUDED.scope_id,
                auto_assign = EXCLUDED.auto_assign,
                deleted = FALSE
        """).bindparams(
            id=_PRESET_ID, name=_PRESET_NAME, scope_type=_SCOPE_TYPE, scope_name=_SCOPE_NAME
        )
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


def _create_role(conn: sa.engine.Connection) -> None:
    """Instantiate the preset in its scope the way provisioning does: the role, its node,
    its scope's own edge and binding, and the preset's permissions."""
    # The name a preset without a template gives its role in a scope.
    name_prefix = _PRESET_NAME[: _MAX_ROLE_NAME_LENGTH - len("-00000000")]
    role_id = conn.execute(
        sa.text("""
            INSERT INTO roles
                (name, source, status, auto_assign, role_preset_id, scope_type, scope_id)
            SELECT
                :name_prefix || '-' || left(CAST(p.scope_id AS text), 8),
                'system', 'active', TRUE, p.id, p.scope_type, p.scope_id
            FROM role_presets p
            JOIN virtual_entities node
                ON node.entity_type = p.scope_type AND node.entity_id = p.scope_id
            WHERE p.id = CAST(:id AS uuid)
              AND NOT EXISTS (
                SELECT 1 FROM roles r
                WHERE r.role_preset_id = p.id
                  AND r.scope_type = p.scope_type
                  AND r.scope_id = p.scope_id
              )
            RETURNING id
        """).bindparams(name_prefix=name_prefix, id=_PRESET_ID)
    ).scalar()
    if role_id is None:
        return
    conn.execute(
        sa.text("""
            INSERT INTO virtual_entities (entity_type, entity_id)
            VALUES ('role', :role_id)
            ON CONFLICT (entity_type, entity_id) DO NOTHING
        """).bindparams(role_id=role_id)
    )
    conn.execute(
        sa.text("""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT node.id, node.id, FALSE
            FROM virtual_entities node
            WHERE node.entity_type = 'role' AND node.entity_id = :role_id
            UNION ALL
            SELECT scope.id, node.id, FALSE
            FROM roles r
            JOIN virtual_entities node ON node.entity_type = 'role' AND node.entity_id = r.id
            JOIN virtual_entities scope
                ON scope.entity_type = r.scope_type AND scope.entity_id = r.scope_id
            WHERE r.id = :role_id
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """).bindparams(role_id=role_id)
    )
    conn.execute(
        sa.text("""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT node.id, node.id, CAST(NULL AS smallint)
            FROM virtual_entities node
            WHERE node.entity_type = 'role' AND node.entity_id = :role_id
            UNION ALL
            SELECT node.id, scope.id, CAST(NULL AS smallint)
            FROM roles r
            JOIN virtual_entities node ON node.entity_type = 'role' AND node.entity_id = r.id
            JOIN virtual_entities scope
                ON scope.entity_type = r.scope_type AND scope.entity_id = r.scope_id
            WHERE r.id = :role_id
            ON CONFLICT DO NOTHING
        """).bindparams(role_id=role_id)
    )
    conn.execute(
        sa.text("""
            INSERT INTO permissions (role_id, entity_type, permission)
            SELECT :role_id, p.entity_type, p.permission
            FROM role_permission_presets p
            WHERE p.role_preset_id = CAST(:id AS uuid) AND p.permission <> 0
        """).bindparams(role_id=role_id, id=_PRESET_ID)
    )


def upgrade() -> None:
    op.add_column("role_presets", sa.Column("scope_id", GUID(), nullable=True))
    conn = op.get_bind()
    _write_preset(conn)
    _create_role(conn)


def downgrade() -> None:
    """The preset and its role stay: a revision before this one creates no role of the
    ``global`` type."""
    op.drop_column("role_presets", "scope_id")
