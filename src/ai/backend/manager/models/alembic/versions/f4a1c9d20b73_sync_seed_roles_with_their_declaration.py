"""Sync the seed roles with their declaration

The seed roles are declared under `data/permission/seed/roles/`, and the fixture is
generated from it. A database seeded before that carries what the data migrations
left behind instead, so the two disagree.

Rewrite the presets the declaration states, then the permissions of every role
instantiated from one. A role no preset instantiated is left alone: it was made by
hand, and nothing here answers for it.

Retire the names that are no longer entity types: `model_deployment` is now
`deployment`, the two admin pages are now `scope_admin`, and `keypair`,
`vfolder:data` and `session:app_service` are fields whose owning entity answers for
them.

Revision ID: f4a1c9d20b73
Revises: c58b0d3a9e14
Create Date: 2026-09-14

"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f4a1c9d20b73"
down_revision = "c58b0d3a9e14"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


@dataclass(frozen=True)
class _Preset:
    """One declared preset, as this revision froze it."""

    id: str
    name: str
    scope_type: str
    auto_assign: bool
    grants: tuple[tuple[str, tuple[int, ...]], ...]


_PRESETS: Final[tuple[_Preset, ...]] = (
    _Preset(
        id="9ebf4f57-9e67-5631-997a-d2d79cc3815f",
        name="domain_admin",
        scope_type="domain",
        auto_assign=False,
        grants=(
            ("agent", (1,)),
            (
                "app_config_fragment",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("container_registry", (1,)),
            (
                "deployment",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "deployment_preset",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "domain",
                (
                    1,
                    2,
                ),
            ),
            (
                "entity_share",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "idle_checker",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "image",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "model_card",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "network",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "project",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "project_resource_policy",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("resource_group", (1,)),
            (
                "resource_preset",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "role",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "scope_admin",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "session",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "session_group",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "session_template",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "user",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "user_resource_policy",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "vfolder",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
        ),
    ),
    _Preset(
        id="22c4db03-24aa-5ff8-b5a9-64b2a2182413",
        name="project_admin",
        scope_type="project",
        auto_assign=False,
        grants=(
            ("agent", (1,)),
            (
                "app_config_fragment",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("container_registry", (1,)),
            (
                "deployment",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("domain", (1,)),
            (
                "entity_share",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "idle_checker",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "image",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "model_card",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "network",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "project",
                (
                    1,
                    2,
                    8,
                    16,
                ),
            ),
            ("project_resource_policy", (1,)),
            ("resource_group", (1,)),
            (
                "resource_preset",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "role",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "scope_admin",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "session",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "session_group",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "session_template",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("user", (1,)),
            (
                "vfolder",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
        ),
    ),
    _Preset(
        id="06057849-3534-546f-b74c-b79d5d3ecf5e",
        name="project_member",
        scope_type="project",
        auto_assign=True,
        grants=(
            ("agent", (1,)),
            ("app_config_fragment", (1,)),
            ("container_registry", (1,)),
            ("deployment", (4,)),
            ("image", (1,)),
            ("model_card", (1,)),
            ("resource_group", (1,)),
            ("resource_preset", (1,)),
            ("session", (4,)),
            ("session_group", (4,)),
            ("user", (1,)),
            (
                "vfolder",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
        ),
    ),
    _Preset(
        id="776c1366-dcf3-5abd-b8de-bc3ad3b759ad",
        name="user_owner",
        scope_type="user",
        auto_assign=False,
        grants=(
            ("agent", (1,)),
            (
                "app_config_fragment",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("container_registry", (1,)),
            (
                "deployment",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("domain", (1,)),
            (
                "entity_share",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "idle_checker",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "image",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "network",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("resource_group", (1,)),
            (
                "resource_preset",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            ("role", (1,)),
            (
                "session",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "session_group",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "session_template",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
            (
                "user",
                (
                    1,
                    2,
                    8,
                    16,
                ),
            ),
            ("user_resource_policy", (1,)),
            (
                "vfolder",
                (
                    1,
                    2,
                    4,
                    8,
                    16,
                ),
            ),
        ),
    ),
)

# The entity type each retired name is answered by now, or None where the owning
# entity answers and the row goes.
_RETIRED: Final[dict[str, str | None]] = {
    "model_deployment": "deployment",
    "project_admin_page": "scope_admin",
    "domain_admin_page": "scope_admin",
    "keypair": None,
    "vfolder:data": None,
    "session:app_service": None,
}


def _retire_names(conn: sa.engine.Connection) -> None:
    for name, replacement in _RETIRED.items():
        if replacement is None:
            conn.execute(
                sa.text("DELETE FROM permissions WHERE entity_type = :name").bindparams(name=name)
            )
            continue
        # A role may already hold the replacement, and the pair is unique.
        conn.execute(
            sa.text("""
                DELETE FROM permissions p
                WHERE p.entity_type = :name
                  AND EXISTS (
                      SELECT 1 FROM permissions q
                      WHERE q.role_id = p.role_id
                        AND q.entity_type = :replacement
                        AND q.permission = p.permission
                  )
            """).bindparams(name=name, replacement=replacement)
        )
        conn.execute(
            sa.text(
                "UPDATE permissions SET entity_type = :replacement WHERE entity_type = :name"
            ).bindparams(name=name, replacement=replacement)
        )


def _write_presets(conn: sa.engine.Connection) -> None:
    for preset in _PRESETS:
        conn.execute(
            sa.text("""
                INSERT INTO role_presets (id, name, scope_type, auto_assign, deleted)
                VALUES (:id, :name, :scope_type, :auto_assign, false)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    scope_type = EXCLUDED.scope_type,
                    auto_assign = EXCLUDED.auto_assign,
                    deleted = false
            """).bindparams(
                id=preset.id,
                name=preset.name,
                scope_type=preset.scope_type,
                auto_assign=preset.auto_assign,
            )
        )
        conn.execute(
            sa.text("DELETE FROM role_permission_presets WHERE role_preset_id = :id").bindparams(
                id=preset.id
            )
        )
        rows = [
            {
                "id": str(uuid.uuid4()),
                "role_preset_id": preset.id,
                "entity_type": entity_type,
                "permission": bit,
            }
            for entity_type, bits in preset.grants
            for bit in bits
        ]
        if rows:
            conn.execute(
                sa.text("""
                    INSERT INTO role_permission_presets
                        (id, role_preset_id, entity_type, permission)
                    VALUES (:id, :role_preset_id, :entity_type, :permission)
                """),
                rows,
            )


def _write_role_permissions(conn: sa.engine.Connection) -> None:
    for preset in _PRESETS:
        role_ids = [
            row.id
            for row in conn.execute(
                sa.text("SELECT id FROM roles WHERE role_preset_id = :id").bindparams(id=preset.id)
            )
        ]
        if not role_ids:
            continue
        conn.execute(
            sa.text("DELETE FROM permissions WHERE role_id = ANY(:role_ids)").bindparams(
                role_ids=role_ids
            )
        )
        rows = [
            {
                "id": str(uuid.uuid4()),
                "role_id": role_id,
                "entity_type": entity_type,
                "permission": bit,
            }
            for role_id in role_ids
            for entity_type, bits in preset.grants
            for bit in bits
        ]
        if rows:
            conn.execute(
                sa.text("""
                    INSERT INTO permissions (id, role_id, entity_type, permission)
                    VALUES (:id, :role_id, :entity_type, :permission)
                """),
                rows,
            )


def upgrade() -> None:
    conn = op.get_bind()
    _retire_names(conn)
    _write_presets(conn)
    _write_role_permissions(conn)


def downgrade() -> None:
    """The rows this replaced are not recoverable; the seed states what they are now."""
