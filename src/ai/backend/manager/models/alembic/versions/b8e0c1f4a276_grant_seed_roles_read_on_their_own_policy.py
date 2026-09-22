"""Grant the seed roles read on the policy their scope is subject to

`user_owner` gains read on `keypair_resource_policy` and `project_member` on
`project_resource_policy`, as the role files now state. The roles the presets already
made carry the grant too, so an installation seeded before this reads its own policies
the way a fresh one does.

Revision ID: b8e0c1f4a276
Revises: e4c1b9d7a250
Create Date: 2026-09-22

"""

from __future__ import annotations

import hashlib
import uuid
from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8e0c1f4a276"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e4c1b9d7a250"
branch_labels = None
depends_on = None

_READ: Final[int] = 1

# The seed derives an id as a uuid7 whose timestamp is fixed and whose remaining bits
# come from what it identifies, so a database migrated here and one seeded from the
# fixture hold the same rows.
_EPOCH_MS: Final[int] = 1757670718265

# The preset each grant is added to, as (preset id, entity type).
_GRANTS: Final[tuple[tuple[str, str], ...]] = (
    # user_owner
    ("776c1366-dcf3-5abd-b8de-bc3ad3b759ad", "keypair_resource_policy"),
    # project_member
    ("06057849-3534-546f-b74c-b79d5d3ecf5e", "project_resource_policy"),
)


def _identify(*parts: str) -> str:
    digest = hashlib.blake2b("|".join(parts).encode("utf-8"), digest_size=10).digest()
    value = (_EPOCH_MS & 0xFFFFFFFFFFFF) << 80 | int.from_bytes(digest, "big")
    value &= ~(0xF << 76)
    value |= 0x7 << 76
    value &= ~(0x3 << 62)
    value |= 0x2 << 62
    return str(uuid.UUID(int=value))


def upgrade() -> None:
    conn = op.get_bind()
    for preset_id, entity_type in _GRANTS:
        conn.execute(
            sa.text("""
                INSERT INTO role_permission_presets
                    (id, role_preset_id, entity_type, permission)
                VALUES (
                    CAST(:id AS uuid), CAST(:preset_id AS uuid), :entity_type, :permission
                )
                ON CONFLICT DO NOTHING
            """).bindparams(
                id=_identify("role_permission_preset", preset_id, entity_type, str(_READ)),
                preset_id=preset_id,
                entity_type=entity_type,
                permission=_READ,
            )
        )
        role_ids = [
            row.id
            for row in conn.execute(
                sa.text(
                    "SELECT id FROM roles WHERE role_preset_id = CAST(:preset_id AS uuid)"
                ).bindparams(preset_id=preset_id)
            )
        ]
        if not role_ids:
            continue
        conn.execute(
            sa.text("""
                INSERT INTO permissions (id, role_id, entity_type, permission)
                VALUES (CAST(:id AS uuid), :role_id, :entity_type, :permission)
                ON CONFLICT DO NOTHING
            """),
            [
                {
                    "id": _identify("permission", str(role_id), entity_type, str(_READ)),
                    "role_id": role_id,
                    "entity_type": entity_type,
                    "permission": _READ,
                }
                for role_id in role_ids
            ],
        )


def downgrade() -> None:
    conn = op.get_bind()
    for preset_id, entity_type in _GRANTS:
        conn.execute(
            sa.text("""
                DELETE FROM permissions
                WHERE entity_type = :entity_type
                  AND permission = :permission
                  AND role_id IN (
                      SELECT id FROM roles WHERE role_preset_id = CAST(:preset_id AS uuid)
                  )
            """).bindparams(entity_type=entity_type, permission=_READ, preset_id=preset_id)
        )
        conn.execute(
            sa.text("""
                DELETE FROM role_permission_presets
                WHERE role_preset_id = CAST(:preset_id AS uuid)
                  AND entity_type = :entity_type
                  AND permission = :permission
            """).bindparams(preset_id=preset_id, entity_type=entity_type, permission=_READ)
        )
