"""Grant the role presets their permissions on system session environ

Every user reads the bindings at public, a domain's or a project's members read the ones at
their domain or project, and its admins manage them. Write the grants to the presets and to
every role made from them.

Revision ID: bf07cae92d86
Revises: fa2dfd48c169
Create Date: 2026-10-21

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.role_permission_preset.ids import (
    role_permission_preset_id,
)

# revision identifiers, used by Alembic.
revision = "bf07cae92d86"  # Part of: NEXT_RELEASE_VERSION
down_revision = "fa2dfd48c169"
branch_labels = None
depends_on = None


_PUBLIC_MEMBER_PRESET_ID: Final[str] = "01993d56-bb39-7d13-a84b-b6a84fc8b7fd"
_DOMAIN_MEMBER_PRESET_ID: Final[str] = "76616aa7-6597-5b11-8629-adff5d5640c2"
_DOMAIN_ADMIN_PRESET_ID: Final[str] = "9ebf4f57-9e67-5631-997a-d2d79cc3815f"
_PROJECT_MEMBER_PRESET_ID: Final[str] = "06057849-3534-546f-b74c-b79d5d3ecf5e"
_PROJECT_ADMIN_PRESET_ID: Final[str] = "22c4db03-24aa-5ff8-b5a9-64b2a2182413"
_ENTITY_TYPE: Final[str] = "system_session_environ"
_READ: Final[int] = int(Permission.READ)
_EVERY_OPERATION: Final[tuple[int, ...]] = tuple(int(bit) for bit in Permission.full())

# (preset id, entity type, permission bit) each grant is written for.
_GRANTS: Final[tuple[tuple[str, str, int], ...]] = (
    (_PUBLIC_MEMBER_PRESET_ID, _ENTITY_TYPE, _READ),
    (_DOMAIN_MEMBER_PRESET_ID, _ENTITY_TYPE, _READ),
    (_PROJECT_MEMBER_PRESET_ID, _ENTITY_TYPE, _READ),
    *((_DOMAIN_ADMIN_PRESET_ID, _ENTITY_TYPE, bit) for bit in _EVERY_OPERATION),
    *((_PROJECT_ADMIN_PRESET_ID, _ENTITY_TYPE, bit) for bit in _EVERY_OPERATION),
)


def grant(conn: sa.engine.Connection, preset_id: str, entity_type: str, permission: int) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO role_permission_presets (id, role_preset_id, entity_type, permission)
            SELECT CAST(:id AS uuid), p.id, :entity_type, :permission
            FROM role_presets p
            WHERE p.id = CAST(:preset_id AS uuid)
            ON CONFLICT DO NOTHING
        """).bindparams(
            id=role_permission_preset_id(preset_id, entity_type, permission),
            preset_id=preset_id,
            entity_type=entity_type,
            permission=permission,
        )
    )
    conn.execute(
        sa.text("""
            INSERT INTO permissions (role_id, entity_type, permission)
            SELECT r.id, :entity_type, :permission
            FROM roles r
            WHERE r.role_preset_id = CAST(:preset_id AS uuid)
            ON CONFLICT (role_id, entity_type, permission) DO NOTHING
        """).bindparams(preset_id=preset_id, entity_type=entity_type, permission=permission)
    )


def revoke(conn: sa.engine.Connection, preset_id: str, entity_type: str, permission: int) -> None:
    conn.execute(
        sa.text("""
            DELETE FROM permissions
            WHERE entity_type = :entity_type
              AND permission = :permission
              AND role_id IN (SELECT id FROM roles WHERE role_preset_id = CAST(:preset_id AS uuid))
        """).bindparams(preset_id=preset_id, entity_type=entity_type, permission=permission)
    )
    conn.execute(
        sa.text("""
            DELETE FROM role_permission_presets
            WHERE role_preset_id = CAST(:preset_id AS uuid)
              AND entity_type = :entity_type
              AND permission = :permission
        """).bindparams(preset_id=preset_id, entity_type=entity_type, permission=permission)
    )


def upgrade() -> None:
    conn = op.get_bind()
    for preset_id, entity_type, permission in _GRANTS:
        grant(conn, preset_id, entity_type, permission)


def downgrade() -> None:
    conn = op.get_bind()
    for preset_id, entity_type, permission in _GRANTS:
        revoke(conn, preset_id, entity_type, permission)
