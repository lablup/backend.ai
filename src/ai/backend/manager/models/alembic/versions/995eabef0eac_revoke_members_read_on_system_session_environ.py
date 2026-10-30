"""Revoke the domain and project members' read on system session environ

The graph binds a project under its domain, so a domain member's READ passed on the rows of
every project in the domain. Only the admins of a domain or a project read its rows. Remove
the grant from the two member presets and from every role made from them.

Revision ID: 995eabef0eac
Revises: a37b92a3e063
Create Date: 2026-10-30

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.cli.role_fixture import _identify

# revision identifiers, used by Alembic.
revision = "995eabef0eac"  # Part of: NEXT_RELEASE_VERSION
down_revision = "a37b92a3e063"
branch_labels = None
depends_on = None


_DOMAIN_MEMBER_PRESET_ID: Final[str] = "76616aa7-6597-5b11-8629-adff5d5640c2"
_PROJECT_MEMBER_PRESET_ID: Final[str] = "06057849-3534-546f-b74c-b79d5d3ecf5e"
_ENTITY_TYPE: Final[str] = "system_session_environ"
_READ: Final[int] = int(Permission.READ)

# (preset id, entity type, permission bit) each revoke is written for.
_REVOKES: Final[tuple[tuple[str, str, int], ...]] = (
    (_DOMAIN_MEMBER_PRESET_ID, _ENTITY_TYPE, _READ),
    (_PROJECT_MEMBER_PRESET_ID, _ENTITY_TYPE, _READ),
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
            id=_identify("role_permission_preset", preset_id, entity_type, str(permission)),
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
    for preset_id, entity_type, permission in _REVOKES:
        revoke(conn, preset_id, entity_type, permission)


def downgrade() -> None:
    conn = op.get_bind()
    for preset_id, entity_type, permission in _REVOKES:
        grant(conn, preset_id, entity_type, permission)
