"""Grant domain members READ on images and user owners READ on projects

A read that takes no scope answers from every scope the caller's roles reach, so the
grant has to be there for the caller's own scope and their domain. Write both to the
presets and to every role made from them.

Revision ID: a1f6b7c4d902
Revises: b8d14e6a0f52
Create Date: 2026-09-21

"""

from __future__ import annotations

import hashlib
import uuid
from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1f6b7c4d902"  # Part of: NEXT_RELEASE_VERSION
down_revision = "b8d14e6a0f52"
branch_labels = None
depends_on = None


_DOMAIN_MEMBER_PRESET_ID: Final[str] = "76616aa7-6597-5b11-8629-adff5d5640c2"
_USER_OWNER_PRESET_ID: Final[str] = "776c1366-dcf3-5abd-b8de-bc3ad3b759ad"
_READ: Final[int] = 1

# (preset id, entity type) each grant is written for.
_GRANTS: Final[tuple[tuple[str, str], ...]] = (
    (_DOMAIN_MEMBER_PRESET_ID, "image"),
    (_USER_OWNER_PRESET_ID, "project"),
)

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


def grant(conn: sa.engine.Connection, preset_id: str, entity_type: str) -> None:
    conn.execute(
        sa.text("""
            INSERT INTO role_permission_presets (id, role_preset_id, entity_type, permission)
            SELECT CAST(:id AS uuid), p.id, :entity_type, :permission
            FROM role_presets p
            WHERE p.id = CAST(:preset_id AS uuid)
            ON CONFLICT DO NOTHING
        """).bindparams(
            id=_identify("role_permission_preset", preset_id, entity_type, str(_READ)),
            preset_id=preset_id,
            entity_type=entity_type,
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
        """).bindparams(preset_id=preset_id, entity_type=entity_type, permission=_READ)
    )


def revoke(conn: sa.engine.Connection, preset_id: str, entity_type: str) -> None:
    conn.execute(
        sa.text("""
            DELETE FROM permissions
            WHERE entity_type = :entity_type
              AND permission = :permission
              AND role_id IN (SELECT id FROM roles WHERE role_preset_id = CAST(:preset_id AS uuid))
        """).bindparams(preset_id=preset_id, entity_type=entity_type, permission=_READ)
    )
    conn.execute(
        sa.text("""
            DELETE FROM role_permission_presets
            WHERE role_preset_id = CAST(:preset_id AS uuid)
              AND entity_type = :entity_type
              AND permission = :permission
        """).bindparams(preset_id=preset_id, entity_type=entity_type, permission=_READ)
    )


def upgrade() -> None:
    conn = op.get_bind()
    for preset_id, entity_type in _GRANTS:
        grant(conn, preset_id, entity_type)


def downgrade() -> None:
    conn = op.get_bind()
    for preset_id, entity_type in _GRANTS:
        revoke(conn, preset_id, entity_type)
