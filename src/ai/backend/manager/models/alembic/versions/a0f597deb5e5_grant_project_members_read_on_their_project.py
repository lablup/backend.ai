"""Grant project members READ on their project

The project_member preset held no grant on the project itself, so a member could not
read the project they belong to. Write the grant to the preset and to every role made
from it.

Revision ID: a0f597deb5e5
Revises: dafe06a6c763
Create Date: 2026-09-17

"""

from __future__ import annotations

import hashlib
import uuid
from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a0f597deb5e5"  # Part of: NEXT_RELEASE_VERSION
down_revision = "dafe06a6c763"
branch_labels = None
depends_on = None


_PRESET_ID: Final[str] = "06057849-3534-546f-b74c-b79d5d3ecf5e"
_ENTITY_TYPE: Final[str] = "project"
_READ: Final[int] = 1

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


def grant(conn: sa.engine.Connection) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO role_permission_presets (id, role_preset_id, entity_type, permission)
            SELECT CAST(:id AS uuid), p.id, :entity_type, :permission
            FROM role_presets p
            WHERE p.id = CAST(:preset_id AS uuid)
            ON CONFLICT DO NOTHING
        """).bindparams(
            id=_identify("role_permission_preset", _PRESET_ID, _ENTITY_TYPE, str(_READ)),
            preset_id=_PRESET_ID,
            entity_type=_ENTITY_TYPE,
            permission=_READ,
        )
    )
    conn.execute(
        sa.text("""
            INSERT INTO permissions (role_id, entity_type, permission)
            SELECT r.id, :entity_type, :permission
            FROM roles r
            WHERE r.role_preset_id = CAST(:preset_id AS uuid)
            ON CONFLICT (role_id, entity_type, permission) DO NOTHING
        """).bindparams(preset_id=_PRESET_ID, entity_type=_ENTITY_TYPE, permission=_READ)
    )


def revoke(conn: sa.engine.Connection) -> None:
    conn.execute(
        sa.text("""
            DELETE FROM permissions
            WHERE entity_type = :entity_type
              AND permission = :permission
              AND role_id IN (SELECT id FROM roles WHERE role_preset_id = CAST(:preset_id AS uuid))
        """).bindparams(preset_id=_PRESET_ID, entity_type=_ENTITY_TYPE, permission=_READ)
    )
    conn.execute(
        sa.text("""
            DELETE FROM role_permission_presets
            WHERE role_preset_id = CAST(:preset_id AS uuid)
              AND entity_type = :entity_type
              AND permission = :permission
        """).bindparams(preset_id=_PRESET_ID, entity_type=_ENTITY_TYPE, permission=_READ)
    )


def upgrade() -> None:
    grant(op.get_bind())


def downgrade() -> None:
    revoke(op.get_bind())
