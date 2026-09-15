"""Sync the seed roles with their declaration

The seed roles are declared under `data/permission/seed/roles/`, and the fixture is
generated from it. A database seeded before that carries what the data migrations
left behind instead, so the two disagree.

Rewrite the presets the declaration states, give every scope the role of each preset
under the name and id the seed gives it, and pass on to it the holders of the system
role its name stood for, under either the data migrations' naming or the runtime's.
A project's creator still on its roster holds its admin role. The system roles no
preset made then go, and every preset role holds what its preset states. A custom
role is left alone: it was made by hand, and nothing here answers for it.

Retire the names that are no longer entity types: `model_deployment` is now
`deployment`, the two admin pages are now `scope_admin`, and `keypair`,
`vfolder:data` and `session:app_service` are fields whose owning entity answers for
them.

Revision ID: f4a1c9d20b73
Revises: c58b0d3a9e14
Create Date: 2026-09-14

"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any, Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f4a1c9d20b73"
down_revision = "c58b0d3a9e14"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


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


class _Preset:
    """One declared preset, as this revision froze it.

    A plain class rather than a dataclass: alembic loads a revision without putting it
    in `sys.modules`, and `@dataclass` reads the module's namespace to resolve its
    annotations."""

    id: str
    name: str
    scope_type: str
    auto_assign: bool
    grants: tuple[tuple[str, tuple[int, ...]], ...]

    def __init__(
        self,
        id: str,
        name: str,
        scope_type: str,
        auto_assign: bool,
        grants: tuple[tuple[str, tuple[int, ...]], ...],
    ) -> None:
        self.id = id
        self.name = name
        self.scope_type = scope_type
        self.auto_assign = auto_assign
        self.grants = grants


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

# Every entity type this build knows, as `mgr ops types` reports them: the entity
# rows and the unclassified ones, which have no identifier class but are permitted
# all the same. A permission row naming anything else is left over from a rename.
_ENTITY_TYPES: Final[frozenset[str]] = frozenset({
    "agent",
    "app_config",
    "app_config_allow_list",
    "app_config_definition",
    "app_config_fragment",
    "artifact",
    "artifact_registry",
    "auth",
    "client_ip_masking_policy",
    "container_registry",
    "deployment",
    "deployment_preset",
    "domain",
    "entity_share",
    "global",
    "idle_checker",
    "image",
    "keypair_resource_policy",
    "login_client_type",
    "model_card",
    "network",
    "notification_channel",
    "notification_rule",
    "object_storage",
    "project",
    "project_resource_policy",
    "prometheus_query_preset",
    "prometheus_query_preset_category",
    "resource_group",
    "resource_preset",
    "resource_slot_type",
    "retention_policy",
    "role",
    "role_preset",
    "runtime_variant",
    "runtime_variant_preset",
    "scope_admin",
    "service_catalog",
    "session",
    "session_group",
    "session_template",
    "storage_namespace",
    "user",
    "user_resource_policy",
    "vfolder",
    "vfolder_invitation",
    "vfs_storage",
})


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


# The prefix the earlier data migrations and the seed give a system role's name. The
# runtime named the roles it made before presets did without it.
_LEGACY_PREFIX: Final[str] = "role_"
_MAX_ROLE_NAME_LENGTH: Final[int] = 64


_PRESET_IDS: Final[dict[str, str]] = {preset.name: preset.id for preset in _PRESETS}


def _preset_for(scope_type: str, scope_id: str, name: str) -> str | None:
    """The id of the preset a system role's name stands for, under either naming rule,
    or None where the name says nothing."""
    short = scope_id[:8]
    if scope_type == "user":
        made = name.startswith(f"{_LEGACY_PREFIX}user_") or name == f"user-{short}"
        return _PRESET_IDS["user_owner"] if made else None
    for kind in ("admin", "member"):
        if scope_type == "project":
            made = name in (f"{_LEGACY_PREFIX}project_{short}_{kind}", f"project-{short}-{kind}")
        elif scope_type == "domain":
            made = (name.startswith(f"{_LEGACY_PREFIX}domain_") and name.endswith(f"_{kind}")) or (
                name.startswith("domain-") and name.endswith(f"-{kind}")
            )
        else:
            return None
        if made:
            return _PRESET_IDS.get(f"{scope_type}_{kind}")
    return None


def _seed_role_name(scope_type: str, scope_id: str, label: str, preset_name: str) -> str:
    """The name the seed gives a preset's role in a scope. `label` is the domain name or
    the username."""
    if scope_type == "user":
        name = f"{_LEGACY_PREFIX}user_{label}"
    elif scope_type == "domain":
        name = f"{_LEGACY_PREFIX}domain_{label}_{preset_name.removeprefix('domain_')}"
    else:
        name = f"{_LEGACY_PREFIX}project_{scope_id[:8]}_{preset_name.removeprefix('project_')}"
    return name[:_MAX_ROLE_NAME_LENGTH]


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
                VALUES (CAST(:id AS uuid), :name, :scope_type, :auto_assign, false)
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
            sa.text(
                "DELETE FROM role_permission_presets WHERE role_preset_id = CAST(:id AS uuid)"
            ).bindparams(id=preset.id)
        )
        rows = [
            {
                "id": _identify("role_permission_preset", preset.id, entity_type, str(bit)),
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
                    VALUES (
                        CAST(:id AS uuid), CAST(:role_preset_id AS uuid), :entity_type,
                        :permission
                    )
                """),
                rows,
            )


def _write_role_permissions(conn: sa.engine.Connection) -> None:
    for preset in _PRESETS:
        role_ids = [
            row.id
            for row in conn.execute(
                sa.text("SELECT id FROM roles WHERE role_preset_id = CAST(:id AS uuid)").bindparams(
                    id=preset.id
                )
            )
        ]
        if not role_ids:
            continue
        conn.execute(
            sa.text("DELETE FROM permissions WHERE role_id = ANY(:role_ids)").bindparams(
                sa.bindparam("role_ids", role_ids, type_=sa.ARRAY(sa.Uuid))
            )
        )
        rows = [
            {
                "id": _identify("permission", str(role_id), entity_type, str(bit)),
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
                    VALUES (CAST(:id AS uuid), :role_id, :entity_type, :permission)
                """),
                rows,
            )


def _sweep_unknown_types(conn: sa.engine.Connection) -> None:
    """Drop the permission rows naming something that is no longer an entity type.

    Stated as what is kept rather than what goes: a name missed by the retirement map
    above would otherwise survive, and every one of them fails to load."""
    conn.execute(
        sa.text("DELETE FROM permissions WHERE entity_type <> ALL(:kept)").bindparams(
            sa.bindparam("kept", sorted(_ENTITY_TYPES), type_=sa.ARRAY(sa.Text))
        )
    )


def _create_seed_roles(conn: sa.engine.Connection) -> None:
    """Give every scope in the graph the role of each preset it lacks, under the name and
    id the seed gives it. A system role already under that id takes the preset instead."""
    linked = {
        (str(row.role_preset_id), str(row.scope_type), str(row.scope_id))
        for row in conn.execute(
            sa.text(
                "SELECT role_preset_id, scope_type, scope_id"
                " FROM roles WHERE role_preset_id IS NOT NULL"
            )
        )
    }
    scopes = conn.execute(
        sa.text("""
            SELECT 'domain' AS scope_type, d.id AS scope_id, CAST(d.name AS text) AS label
            FROM domains d
            JOIN virtual_entities v ON v.entity_type = 'domain' AND v.entity_id = d.id
            UNION ALL
            SELECT 'project', g.id, ''
            FROM groups g
            JOIN virtual_entities v ON v.entity_type = 'project' AND v.entity_id = g.id
            UNION ALL
            SELECT 'user', u.uuid, CAST(u.username AS text)
            FROM users u
            JOIN virtual_entities v ON v.entity_type = 'user' AND v.entity_id = u.uuid
        """)
    ).all()
    rows: list[dict[str, Any]] = []
    for scope in scopes:
        scope_type, scope_id = str(scope.scope_type), str(scope.scope_id)
        for preset in _PRESETS:
            if preset.scope_type != scope_type or (preset.id, scope_type, scope_id) in linked:
                continue
            name = _seed_role_name(scope_type, scope_id, str(scope.label), preset.name)
            rows.append({
                "id": _identify("role", scope_type, scope_id, name),
                "name": name,
                "auto_assign": preset.auto_assign,
                "role_preset_id": preset.id,
                "scope_type": scope_type,
                "scope_id": scope_id,
            })
    if not rows:
        return
    conn.execute(
        sa.text("""
            INSERT INTO roles
                (id, name, source, status, auto_assign, role_preset_id, scope_type, scope_id)
            VALUES (
                CAST(:id AS uuid), :name, 'system', 'active', :auto_assign,
                CAST(:role_preset_id AS uuid), :scope_type, CAST(:scope_id AS uuid)
            )
            ON CONFLICT (id) DO UPDATE SET
                role_preset_id = EXCLUDED.role_preset_id,
                auto_assign = EXCLUDED.auto_assign
            WHERE roles.source = 'system' AND roles.role_preset_id IS NULL
        """),
        rows,
    )
    _put_in_graph(conn, [uuid.UUID(row["id"]) for row in rows])


def _put_in_graph(conn: sa.engine.Connection, role_ids: list[uuid.UUID]) -> None:
    """Put the preset roles among `role_ids` in the graph as the runtime does, their nodes
    under the seed's ids: each owns and governs itself and is owned and governed by its scope."""
    kept = [
        row.id
        for row in conn.execute(
            sa.text(
                "SELECT id FROM roles WHERE id = ANY(:ids) AND role_preset_id IS NOT NULL"
            ).bindparams(sa.bindparam("ids", role_ids, type_=sa.ARRAY(sa.Uuid)))
        )
    ]
    if not kept:
        return
    conn.execute(
        sa.text("""
            INSERT INTO virtual_entities (id, entity_type, entity_id)
            VALUES (CAST(:id AS uuid), 'role', CAST(:role_id AS uuid))
            ON CONFLICT (entity_type, entity_id) DO NOTHING
        """),
        [
            {"id": _identify("virtual_entity", "role", str(role_id)), "role_id": str(role_id)}
            for role_id in kept
        ],
    )
    ids = sa.bindparam("role_ids", kept, type_=sa.ARRAY(sa.Uuid))
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
        """).bindparams(ids)
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
        """).bindparams(ids)
    )


def _carry_assignments(conn: sa.engine.Connection) -> None:
    """Give the holders of a system role no preset made the preset role its name stands
    for in the same scope, and a project's creator still on its roster its admin role."""
    targets = {
        (str(row.role_preset_id), str(row.scope_type), str(row.scope_id)): str(row.id)
        for row in conn.execute(
            sa.text(
                "SELECT id, role_preset_id, scope_type, scope_id"
                " FROM roles WHERE role_preset_id IS NOT NULL"
            )
        )
    }
    carried: list[dict[str, Any]] = []
    for row in conn.execute(
        sa.text(
            "SELECT id, scope_type, scope_id, name"
            " FROM roles WHERE role_preset_id IS NULL AND source = 'system'"
        )
    ):
        preset_id = _preset_for(str(row.scope_type), str(row.scope_id), str(row.name))
        if preset_id is None:
            continue
        target = targets.get((preset_id, str(row.scope_type), str(row.scope_id)))
        if target is not None:
            carried.append({"old_role_id": str(row.id), "new_role_id": target})
    if carried:
        conn.execute(
            sa.text("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT user_id, CAST(:new_role_id AS uuid)
                FROM user_roles
                WHERE role_id = CAST(:old_role_id AS uuid)
                ON CONFLICT (user_id, role_id) DO NOTHING
            """),
            carried,
        )
    conn.execute(
        sa.text("""
            INSERT INTO user_roles (user_id, role_id)
            SELECT g.creator_id, r.id
            FROM groups g
            JOIN association_groups_users agu
                ON agu.group_id = g.id AND agu.user_id = g.creator_id
            JOIN roles r
                ON r.scope_type = 'project' AND r.scope_id = g.id
                AND r.role_preset_id = CAST(:preset_id AS uuid)
            ON CONFLICT (user_id, role_id) DO NOTHING
        """).bindparams(preset_id=_PRESET_IDS["project_admin"])
    )


def _drop_unlinked_system_roles(conn: sa.engine.Connection) -> None:
    """Drop the system roles no preset accounts for.

    A preset is the only thing that makes a system role, so one without a preset is
    left over from a rule that no longer runs. A role made by hand is never a system
    one, so nothing of anyone's goes here. The role's permissions and assignments go
    with it, as its foreign keys say; its graph node does not, and is taken here."""
    doomed = [
        row.id
        for row in conn.execute(
            sa.text("SELECT id FROM roles WHERE source = 'system' AND role_preset_id IS NULL")
        )
    ]
    if not doomed:
        return
    conn.execute(
        sa.text("DELETE FROM roles WHERE id = ANY(:ids)").bindparams(
            sa.bindparam("ids", doomed, type_=sa.ARRAY(sa.Uuid))
        )
    )
    # The graph node names its entity by a pair, not a foreign key, so nothing takes it
    # away with the row. Its edges go with the node, which is a foreign key.
    conn.execute(
        sa.text(
            "DELETE FROM virtual_entities WHERE entity_type = 'role' AND entity_id = ANY(:ids)"
        ).bindparams(sa.bindparam("ids", doomed, type_=sa.ARRAY(sa.Uuid)))
    )


def _grant_auto_assign_roles(conn: sa.engine.Connection) -> None:
    """Give every project member the roles their project assigns on its own, and put
    them on its roster.

    Which users a project holds is the only part of a seed role's assignment a database
    still states for itself, so the roles a project hands out without being asked are
    the ones recoverable here. Who administers a project is not stated anywhere but the
    assignments `_carry_assignments` passed on.

    The roster edge carries the membership: a role held without it reaches nothing."""
    pairs = conn.execute(
        sa.text("""
            SELECT r.id AS role_id, agu.user_id AS user_id, r.scope_id AS project_id
            FROM roles r
            JOIN association_groups_users agu ON agu.group_id = r.scope_id
            WHERE r.scope_type = 'project'
              AND r.auto_assign IS TRUE
              AND r.status = 'active'
        """)
    ).all()
    for pair in pairs:
        conn.execute(
            sa.text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                ON CONFLICT (user_id, role_id) DO NOTHING
            """).bindparams(user_id=pair.user_id, role_id=pair.role_id)
        )
        _share_membership(conn, str(pair.project_id), str(pair.user_id))


def _share_membership(conn: sa.engine.Connection, project_id: str, user_id: str) -> None:
    """Put the user on the project's roster: the share edge and the read cap on it.

    Left alone where it already stands, so a project whose roster the graph already
    holds keeps the caps it was given."""
    membership_id = conn.execute(
        sa.text("""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT scope.id, member.id, TRUE
            FROM virtual_entities scope, virtual_entities member
            WHERE scope.entity_type = 'project' AND scope.entity_id = CAST(:project_id AS uuid)
              AND member.entity_type = 'user' AND member.entity_id = CAST(:user_id AS uuid)
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
            RETURNING id
        """).bindparams(project_id=project_id, user_id=user_id)
    ).scalar()
    if membership_id is None:
        return
    conn.execute(
        sa.text("""
            INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
            VALUES (:membership_id, 1, TRUE)
        """).bindparams(membership_id=membership_id)
    )


def upgrade() -> None:
    conn = op.get_bind()
    _retire_names(conn)
    _sweep_unknown_types(conn)
    _write_presets(conn)
    _create_seed_roles(conn)
    _carry_assignments(conn)
    _drop_unlinked_system_roles(conn)
    _write_role_permissions(conn)
    _grant_auto_assign_roles(conn)


def downgrade() -> None:
    """The rows this replaced are not recoverable; the seed states what they are now."""
