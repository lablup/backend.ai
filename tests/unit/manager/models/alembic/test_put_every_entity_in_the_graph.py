"""Verifies the entity graph backfill migration against a real database.

Static analysis does not reach the migration's SQL, so the data migration is exercised
here: rows written without their graph rows go in, the migration runs, and the graph
rows it wrote are read back. Every source the migration names is exercised with a row.
"""

from __future__ import annotations

import importlib
import itertools
import pkgutil
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Final

import pytest
import sqlalchemy as sa
from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncConnection

import ai.backend.common.data.entity
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.alembic.versions.dafe06a6c763_put_every_entity_in_the_graph import (
    CREATED_IN_SOURCES,
    NODE_SOURCES,
    PROJECT_ADMIN_PRESET_ID,
    RELATION_SOURCES,
    put_every_entity_in_the_graph,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.base import metadata
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.network.row import NetworkRow
from ai.backend.manager.models.notification.row import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.project.row import AssocGroupUserRow
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.resource_group.row import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.storage_backend.row import StorageBackendRow
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.models.storage_volume.row import StorageVolumeRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import with_tables

# Every row class the migration reads. Importing them registers their tables, which a
# test sandbox does not do on its own.
_ROWS: Final = (
    AgentRow,
    AppConfigAllowListRow,
    AppConfigDefinitionRow,
    AppConfigFragmentRow,
    ArtifactRow,
    AssocGroupUserRow,
    AssociationContainerRegistriesGroupsRow,
    ClientIPMaskingPolicyRow,
    ContainerRegistryRow,
    DeploymentRevisionPresetRow,
    DomainRow,
    EndpointRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
    EntityMembershipRow,
    EntityShareRow,
    HuggingFaceRegistryRow,
    IdleCheckerBindingRow,
    IdleCheckerRow,
    ImageRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    LoginClientTypeRow,
    ModelCardRow,
    NetworkRow,
    NotificationChannelRow,
    NotificationRuleRow,
    ObjectStorageRow,
    PermissionRow,
    ProjectResourcePolicyRow,
    ProjectRow,
    PrometheusQueryPresetCategoryRow,
    PrometheusQueryPresetRow,
    ReservoirRegistryRow,
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    RetentionPolicyRow,
    RoleRow,
    RolePermissionPresetRow,
    RolePresetRow,
    RuntimeVariantPresetRow,
    RuntimeVariantRow,
    ScopeBindingRow,
    ServiceCatalogRow,
    SessionGroupRow,
    SessionIdleCheckRow,
    SessionRow,
    SessionTemplateRow,
    StorageBackendRow,
    StorageNamespaceRow,
    StorageVolumeRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
    VFSStorageRow,
    VFolderRow,
    VirtualEntityRow,
)

# Entity types that name no table of their own.
_TABLELESS_ENTITY_TYPES: Final = frozenset({"app_config", "global", "scope_admin"})

_ALL_BITS: Final = {1, 2, 4, 8, 16}

# Values a table's constraints call for that its column types do not tell, used where the
# caller names none.
_TABLE_DEFAULTS: Final[dict[str, dict[str, Any]]] = {
    "app_config_fragments": {"scope_type": "public", "scope_id": None},
    "entity_shares": {"recipient_email": "bob@test.local"},
    "idle_checkers": {"spec": '{"type": "session_lifetime"}'},
}


def _tables() -> list[Table]:
    """Every table the migration reads, with the tables they reference, parents first."""
    names = {row.__table__.name for row in _ROWS}
    frontier = list(names)
    while frontier:
        for fk in metadata.tables[frontier.pop()].foreign_keys:
            referred = fk.column.table.name
            if referred not in names:
                names.add(referred)
                frontier.append(referred)
    return [table for table in metadata.sorted_tables if table.name in names]


class _Rows:
    """Writes a row into any table, filling each required column from the live schema
    and writing a parent row for each required foreign key the caller did not name."""

    _MAX_DEPTH: Final = 8

    _conn: AsyncConnection
    _seq: itertools.count[int]

    def __init__(self, conn: AsyncConnection) -> None:
        self._conn = conn
        self._seq = itertools.count(1)

    async def insert(self, table: str, **values: Any) -> sa.RowMapping:
        return await self._insert(table, values, 0)

    async def _insert(self, table: str, values: dict[str, Any], depth: int) -> sa.RowMapping:
        assert depth < self._MAX_DEPTH, f"foreign keys of {table} do not bottom out"
        values = {**_TABLE_DEFAULTS.get(table, {}), **values}
        columns = {
            row.name: row
            for row in (
                await self._conn.execute(
                    sa.text("""
                        SELECT a.attname AS name,
                               NOT a.attnotnull AS nullable,
                               (a.atthasdef OR a.attidentity <> '' OR a.attgenerated <> '')
                                   AS has_default,
                               t.typname AS type_name, t.typtype::text AS type_kind,
                               t.typcategory::text AS category,
                               (SELECT e.enumlabel FROM pg_enum e WHERE e.enumtypid = t.oid
                                ORDER BY e.enumsortorder LIMIT 1) AS first_label
                        FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid
                        WHERE a.attrelid = CAST(:table AS regclass)
                          AND a.attnum > 0 AND NOT a.attisdropped
                    """),
                    {"table": table},
                )
            ).all()
        }
        foreign_keys = (
            await self._conn.execute(
                sa.text("""
                    SELECT c.confrelid::regclass::text AS parent,
                           ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k (n, i)
                                 JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.n
                                 ORDER BY k.i) AS local_columns,
                           ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k (n, i)
                                 JOIN pg_attribute a ON a.attrelid = c.confrelid AND a.attnum = k.n
                                 ORDER BY k.i) AS remote_columns
                    FROM pg_constraint c
                    WHERE c.conrelid = CAST(:table AS regclass) AND c.contype = 'f'
                """),
                {"table": table},
            )
        ).all()
        for fk in foreign_keys:
            named = {
                remote: values[local]
                for local, remote in zip(fk.local_columns, fk.remote_columns, strict=True)
                if local in values
            }
            if len(named) == len(fk.local_columns) or None in named.values():
                continue
            if not named and all(columns[column].nullable for column in fk.local_columns):
                continue
            parent = await self._insert(fk.parent.strip('"'), named, depth + 1)
            for local, remote in zip(fk.local_columns, fk.remote_columns, strict=True):
                values[local] = parent[remote]
        for name, column in columns.items():
            if name not in values and not column.nullable and not column.has_default:
                values[name] = self._placeholder(table, column)
        names = list(values)
        quoted = ", ".join(f'"{name}"' for name in names)
        placeholders = ", ".join(f":v{i}" for i in range(len(names)))
        statement = sa.text(f"INSERT INTO {table} ({quoted}) VALUES ({placeholders}) RETURNING *")
        params = {f"v{i}": values[name] for i, name in enumerate(names)}
        return (await self._conn.execute(statement, params)).mappings().one()

    def _placeholder(self, table: str, column: sa.Row[Any]) -> Any:
        n = next(self._seq)
        if column.type_kind == "e":
            return column.first_label
        if column.category == "A":
            return []
        match column.type_name:
            case "varchar" | "text" | "bpchar" | "citext":
                return f"t{n}"
            case "int2" | "int4" | "int8":
                return 1
            case "numeric":
                return Decimal(1)
            case "float4" | "float8":
                return 1.0
            case "bool":
                return False
            case "uuid":
                return uuid.uuid4()
            case "timestamptz":
                return datetime.now(UTC)
            case "timestamp":
                return datetime.now(UTC).replace(tzinfo=None)
            case "date":
                return datetime.now(UTC).date()
            case "interval":
                return timedelta(0)
            case "json" | "jsonb":
                return "{}"
            case "bytea":
                return b""
            case "inet" | "cidr":
                return "127.0.0.1"
        raise AssertionError(f"No placeholder for {table}.{column.name} ({column.type_name})")


@dataclass
class _Scopes:
    domain: sa.RowMapping
    user: sa.RowMapping
    project: sa.RowMapping
    personal_project: sa.RowMapping
    resource_group: sa.RowMapping
    registry: sa.RowMapping
    idle_checker: sa.RowMapping


async def _add_member(rows: _Rows, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """A project member's edge as the scope association table's move left it: own, no cap,
    between nodes that have no self rows yet."""
    project = await rows.insert("virtual_entities", entity_type="project", entity_id=project_id)
    user = await rows.insert("virtual_entities", entity_type="user", entity_id=user_id)
    await rows.insert(
        "entity_memberships",
        virtual_entity_id=project["id"],
        member_entity_id=user["id"],
        capped=False,
    )


async def _scopes(rows: _Rows) -> _Scopes:
    """A user in a domain with their personal project, a team project the user is on, and
    a resource group, a registry and an idle checker. Only the membership is in the graph."""
    domain = await rows.insert("domains")
    user = await rows.insert("users", domain_name=domain["name"], domain_id=domain["id"])
    project = await rows.insert("groups", domain_name=domain["name"], type="general")
    personal_project = await rows.insert(
        "groups", domain_name=domain["name"], type="personal", creator_id=user["uuid"]
    )
    await _add_member(rows, project["id"], user["uuid"])
    return _Scopes(
        domain=domain,
        user=user,
        project=project,
        personal_project=personal_project,
        resource_group=await rows.insert("scaling_groups"),
        registry=await rows.insert("container_registries"),
        idle_checker=await rows.insert("idle_checkers"),
    )


async def _add_node(conn: AsyncConnection, entity_type: str, entity_id: uuid.UUID) -> None:
    """A node for a row a foreign key names by its node, the way the runtime had it."""
    await conn.execute(
        sa.text(
            "INSERT INTO virtual_entities (entity_type, entity_id) VALUES (:t, :i)"
            " ON CONFLICT DO NOTHING"
        ),
        {"t": entity_type, "i": entity_id},
    )


async def _node(conn: AsyncConnection, entity_type: str, entity_id: uuid.UUID) -> uuid.UUID:
    node = await conn.scalar(
        sa.text("SELECT id FROM virtual_entities WHERE entity_type = :t AND entity_id = :i"),
        {"t": entity_type, "i": entity_id},
    )
    assert node is not None, f"no node for {entity_type} {entity_id}"
    return uuid.UUID(str(node))


async def _owners(conn: AsyncConnection, node: uuid.UUID) -> dict[uuid.UUID, bool]:
    """The nodes other than itself holding the node, each with whether it is capped."""
    rows = await conn.execute(
        sa.text(
            "SELECT virtual_entity_id, capped FROM entity_memberships"
            " WHERE member_entity_id = :n AND virtual_entity_id <> :n"
        ),
        {"n": node},
    )
    return {row.virtual_entity_id: row.capped for row in rows}


async def _governors(conn: AsyncConnection, node: uuid.UUID) -> dict[uuid.UUID, int | None]:
    """The scopes other than itself governing the node, each with its cap."""
    rows = await conn.execute(
        sa.text(
            "SELECT scope_entity_id, permission_cap FROM scope_bindings"
            " WHERE virtual_entity_id = :n AND scope_entity_id <> :n"
        ),
        {"n": node},
    )
    return {row.scope_entity_id: row.permission_cap for row in rows}


async def _caps(conn: AsyncConnection, owner: uuid.UUID, member: uuid.UUID) -> set[int]:
    rows = await conn.execute(
        sa.text("""
            SELECT c.permission FROM entity_membership_caps c
            JOIN entity_memberships m ON m.id = c.membership_id
            WHERE m.virtual_entity_id = :o AND m.member_entity_id = :m AND c.all_fields
        """),
        {"o": owner, "m": member},
    )
    return {int(row.permission) for row in rows}


async def _run(conn: AsyncConnection) -> None:
    await conn.run_sync(put_every_entity_in_the_graph)


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _tables()):
        yield database_connection


# -- created_in ---------------------------------------------------------------------------

type _Scope = tuple[str, uuid.UUID]
type _Created = tuple[str, uuid.UUID, list[_Scope]]
# Writes the entity row and answers its type, its id, and the scopes it was created in.
type _CreatedInCase = Callable[[AsyncConnection, _Rows, _Scopes], Awaitable[_Created]]


async def _agent(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert("agents", resource_group_id=s.resource_group["id"])
    return "agent", row["uuid"], [("resource_group", s.resource_group["id"])]


async def _domain_fragment(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert("app_config_fragments", scope_type="domain", scope_id=s.domain["id"])
    return "app_config_fragment", row["id"], [("domain", s.domain["id"])]


async def _user_fragment(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert("app_config_fragments", scope_type="user", scope_id=s.user["uuid"])
    return "app_config_fragment", row["id"], [("user", s.user["uuid"])]


async def _public_fragment(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert("app_config_fragments", scope_type="public", scope_id=None)
    return "app_config_fragment", row["id"], []


async def _deployment(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert(
        "endpoints",
        project=s.project["id"],
        session_owner=s.user["uuid"],
        domain=s.domain["name"],
    )
    return "deployment", row["id"], [("project", s.project["id"]), ("user", s.user["uuid"])]


async def _entity_share(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    await _add_node(conn, "project", s.project["id"])
    row = await rows.insert(
        "entity_shares",
        target_entity_type="project",
        target_entity_id=s.project["id"],
        recipient_email="bob@test.local",
        status="pending",
    )
    return "entity_share", row["id"], [("project", s.project["id"])]


async def _customized_image(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert(
        "images", registry_id=s.registry["id"], customized=True, creator_id=s.user["uuid"]
    )
    scopes = [("container_registry", s.registry["id"]), ("project", s.personal_project["id"])]
    return "image", row["id"], scopes


async def _scanned_image(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert(
        "images", registry_id=s.registry["id"], customized=False, creator_id=s.user["uuid"]
    )
    return "image", row["id"], [("container_registry", s.registry["id"])]


async def _model_card(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert("model_cards", project=s.project["id"], domain=s.domain["name"])
    return "model_card", row["id"], [("project", s.project["id"])]


async def _network(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert("networks", project=s.project["id"], domain_name=s.domain["name"])
    return "network", row["id"], [("project", s.project["id"])]


async def _project(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    return "project", s.project["id"], [("domain", s.domain["id"])]


async def _role(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    await _add_node(conn, "project", s.project["id"])
    row = await rows.insert("roles", scope_type="project", scope_id=s.project["id"])
    return "role", row["id"], [("project", s.project["id"])]


async def _session(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert(
        "sessions", user_uuid=s.user["uuid"], group_id=s.project["id"], domain_name=s.domain["name"]
    )
    return "session", row["id"], [("user", s.user["uuid"]), ("project", s.project["id"])]


async def _session_group(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert(
        "session_groups", project_id=s.project["id"], owner_user_id=s.user["uuid"]
    )
    return "session_group", row["id"], [("project", s.project["id"]), ("user", s.user["uuid"])]


async def _project_template(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert(
        "session_templates",
        user_uuid=s.user["uuid"],
        group_id=s.project["id"],
        domain_name=s.domain["name"],
    )
    scopes = [("user", s.user["uuid"]), ("project", s.project["id"])]
    return "session_template", row["id"], scopes


async def _personal_template(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert(
        "session_templates", user_uuid=s.user["uuid"], group_id=None, domain_name=s.domain["name"]
    )
    return "session_template", row["id"], [("user", s.user["uuid"])]


async def _user(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    return "user", s.user["uuid"], [("domain", s.domain["id"])]


async def _vfolder(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert(
        "vfolders", group=s.project["id"], user=None, domain_name=s.domain["name"]
    )
    return "vfolder", row["id"], [("project", s.project["id"])]


async def _vfolder_without_project(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Created:
    row = await rows.insert("vfolders", group=None, user=None, domain_name=s.domain["name"])
    return "vfolder", row["id"], []


_CREATED_IN_CASES: Final[dict[str, _CreatedInCase]] = {
    "agent": _agent,
    "domain_fragment": _domain_fragment,
    "user_fragment": _user_fragment,
    "public_fragment": _public_fragment,
    "deployment": _deployment,
    "entity_share": _entity_share,
    "customized_image": _customized_image,
    "scanned_image": _scanned_image,
    "model_card": _model_card,
    "network": _network,
    "project": _project,
    "role": _role,
    "session": _session,
    "session_group": _session_group,
    "project_template": _project_template,
    "personal_template": _personal_template,
    "user": _user,
    "vfolder": _vfolder,
    "vfolder_without_project": _vfolder_without_project,
}


# -- relations ----------------------------------------------------------------------------

type _Linked = tuple[_Scope, _Scope]
# Writes the relation row and answers the target and the scope it links.
type _RelationCase = Callable[[AsyncConnection, _Rows, _Scopes], Awaitable[_Linked]]


async def _registry_for_project(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Linked:
    await rows.insert(
        "association_container_registries_groups",
        registry_id=s.registry["id"],
        group_id=s.project["id"],
    )
    return ("container_registry", s.registry["id"]), ("project", s.project["id"])


async def _checker_for_project(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Linked:
    await rows.insert(
        "idle_checker_bindings",
        idle_checker_id=s.idle_checker["id"],
        scope_type="project",
        scope_id=s.project["id"],
    )
    return ("idle_checker", s.idle_checker["id"]), ("project", s.project["id"])


async def _checker_for_session(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Linked:
    session = await rows.insert(
        "sessions", user_uuid=s.user["uuid"], group_id=s.project["id"], domain_name=s.domain["name"]
    )
    await rows.insert(
        "session_idle_checks", idle_checker_id=s.idle_checker["id"], session_id=session["id"]
    )
    return ("idle_checker", s.idle_checker["id"]), ("session", session["id"])


async def _resource_group_for_domain(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Linked:
    await rows.insert(
        "sgroups_for_domains", resource_group_id=s.resource_group["id"], domain_id=s.domain["id"]
    )
    return ("resource_group", s.resource_group["id"]), ("domain", s.domain["id"])


async def _resource_group_for_project(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Linked:
    await rows.insert(
        "sgroups_for_groups", resource_group_id=s.resource_group["id"], group=s.project["id"]
    )
    return ("resource_group", s.resource_group["id"]), ("project", s.project["id"])


async def _resource_group_for_keypair(conn: AsyncConnection, rows: _Rows, s: _Scopes) -> _Linked:
    keypair = await rows.insert("keypairs", user=s.user["uuid"])
    await rows.insert(
        "sgroups_for_keypairs",
        resource_group_id=s.resource_group["id"],
        access_key=keypair["access_key"],
    )
    return ("resource_group", s.resource_group["id"]), ("user", s.user["uuid"])


_RELATION_CASES: Final[dict[str, _RelationCase]] = {
    "registry_for_project": _registry_for_project,
    "checker_for_project": _checker_for_project,
    "checker_for_session": _checker_for_session,
    "resource_group_for_domain": _resource_group_for_domain,
    "resource_group_for_project": _resource_group_for_project,
    "resource_group_for_keypair": _resource_group_for_keypair,
}


class TestSources:
    def test_every_entity_type_with_a_table_is_a_node_source(self) -> None:
        for module in pkgutil.iter_modules(ai.backend.common.data.entity.__path__):
            importlib.import_module(f"ai.backend.common.data.entity.{module.name}")
        declared = {kind.name() for kind in EntityType.kinds()} - _TABLELESS_ENTITY_TYPES

        assert declared == {entity_type for entity_type, _, _ in NODE_SOURCES}

    def test_every_created_in_entity_type_has_a_case(self) -> None:
        sourced = {entity_type for entity_type, _ in CREATED_IN_SOURCES}
        cased = {
            "agent",
            "app_config_fragment",
            "deployment",
            "entity_share",
            "image",
            "model_card",
            "network",
            "project",
            "role",
            "session",
            "session_group",
            "session_template",
            "user",
            "vfolder",
        }

        assert sourced == cased

    def test_every_relation_source_has_a_case(self) -> None:
        assert len(RELATION_SOURCES) == len(_RELATION_CASES)


class TestNodes:
    @pytest.mark.parametrize(
        ("entity_type", "table", "id_column"),
        NODE_SOURCES,
        ids=[table for _, table, _ in NODE_SOURCES],
    )
    async def test_a_row_gets_a_node_owning_and_governing_itself(
        self, db: ExtendedAsyncSAEngine, entity_type: str, table: str, id_column: str
    ) -> None:
        async with db.begin() as conn:
            row = await _Rows(conn).insert(table)

            await _run(conn)

            node = await _node(conn, entity_type, row[id_column])
            assert await conn.scalar(
                sa.text(
                    "SELECT count(*) FROM entity_memberships"
                    " WHERE virtual_entity_id = :n AND member_entity_id = :n AND NOT capped"
                ),
                {"n": node},
            )
            assert await conn.scalar(
                sa.text(
                    "SELECT count(*) FROM scope_bindings WHERE virtual_entity_id = :n"
                    " AND scope_entity_id = :n AND permission_cap IS NULL"
                ),
                {"n": node},
            )


class TestCreatedIn:
    @pytest.mark.parametrize("case", list(_CREATED_IN_CASES.values()), ids=list(_CREATED_IN_CASES))
    async def test_a_row_is_owned_and_governed_by_each_scope_it_was_created_in(
        self, db: ExtendedAsyncSAEngine, case: _CreatedInCase
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            entity_type, entity_id, created_in = await case(conn, rows, scopes)

            await _run(conn)

            node = await _node(conn, entity_type, entity_id)
            scope_nodes = {await _node(conn, t, i) for t, i in created_in}
            owners = await _owners(conn, node)
            governors = await _governors(conn, node)
            assert {owner for owner, capped in owners.items() if not capped} == scope_nodes
            assert {scope for scope, cap in governors.items() if cap is None} == scope_nodes

    async def test_a_share_edge_from_a_creation_scope_becomes_own(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            network = await rows.insert(
                "networks", project=scopes.project["id"], domain_name=scopes.domain["name"]
            )
            await _add_node(conn, "project", scopes.project["id"])
            await _add_node(conn, "network", network["id"])
            project = await _node(conn, "project", scopes.project["id"])
            node = await _node(conn, "network", network["id"])
            membership = await conn.scalar(
                sa.text(
                    "INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)"
                    " VALUES (:p, :n, TRUE) RETURNING id"
                ),
                {"p": project, "n": node},
            )
            await rows.insert(
                "entity_membership_caps", membership_id=membership, permission=1, all_fields=True
            )

            await _run(conn)

            assert (await _owners(conn, node))[project] is False
            assert await _caps(conn, project, node) == set()


class TestRosters:
    async def test_a_member_and_a_personal_project_owner_are_on_a_read_capped_roster(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            scopes = await _scopes(_Rows(conn))

            await _run(conn)

            user = await _node(conn, "user", scopes.user["uuid"])
            for project_id in (scopes.project["id"], scopes.personal_project["id"]):
                project = await _node(conn, "project", project_id)
                assert (await _owners(conn, user))[project] is True
                assert await _caps(conn, project, user) == {1}
                assert project not in await _governors(conn, user)

    async def test_an_own_roster_edge_and_its_binding_become_a_capped_share(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            outsider = await rows.insert(
                "users", domain_name=scopes.domain["name"], domain_id=scopes.domain["id"]
            )
            await _add_node(conn, "project", scopes.project["id"])
            await _add_node(conn, "user", outsider["uuid"])
            project = await _node(conn, "project", scopes.project["id"])
            user = await _node(conn, "user", outsider["uuid"])
            await conn.execute(
                sa.text(
                    "INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)"
                    " VALUES (:p, :u, FALSE)"
                ),
                {"p": project, "u": user},
            )
            await conn.execute(
                sa.text(
                    "INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id)"
                    " VALUES (:u, :p)"
                ),
                {"p": project, "u": user},
            )

            await _run(conn)

            assert (await _owners(conn, user))[project] is True
            assert await _caps(conn, project, user) == {1}
            assert project not in await _governors(conn, user)


class TestLegacyRoster:
    async def test_a_user_only_in_association_groups_users_is_not_on_the_roster(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            removed = await rows.insert(
                "users", domain_name=scopes.domain["name"], domain_id=scopes.domain["id"]
            )
            await rows.insert(
                "association_groups_users", group_id=scopes.project["id"], user_id=removed["uuid"]
            )

            await _run(conn)

            user = await _node(conn, "user", removed["uuid"])
            project = await _node(conn, "project", scopes.project["id"])
            assert project not in await _owners(conn, user)


class TestRelations:
    @pytest.mark.parametrize("case", list(_RELATION_CASES.values()), ids=list(_RELATION_CASES))
    async def test_the_scope_governs_the_target_and_the_target_holds_the_scope_under_read(
        self, db: ExtendedAsyncSAEngine, case: _RelationCase
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            (target_type, target_id), (scope_type, scope_id) = await case(conn, rows, scopes)

            await _run(conn)

            target = await _node(conn, target_type, target_id)
            scope = await _node(conn, scope_type, scope_id)
            assert (await _governors(conn, target))[scope] == 1
            assert (await _owners(conn, scope))[target] is True
            assert await _caps(conn, target, scope) == {1}


class TestAcceptedShares:
    async def _share(
        self,
        conn: AsyncConnection,
        rows: _Rows,
        scopes: _Scopes,
        recipient: _Scope,
        permission_cap: int | None,
    ) -> uuid.UUID:
        """A folder of the team project, accepted by ``recipient``."""
        vfolder = await rows.insert(
            "vfolders", group=scopes.project["id"], user=None, domain_name=scopes.domain["name"]
        )
        await _add_node(conn, "vfolder", vfolder["id"])
        await _add_node(conn, *recipient)
        await rows.insert(
            "entity_shares",
            recipient_entity_type=recipient[0],
            recipient_entity_id=recipient[1],
            target_entity_type="vfolder",
            target_entity_id=vfolder["id"],
            permission_cap=permission_cap,
            status="accepted",
        )
        return uuid.UUID(str(vfolder["id"]))

    async def test_a_share_to_a_user_lands_in_their_personal_project(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            vfolder_id = await self._share(conn, rows, scopes, ("user", scopes.user["uuid"]), 3)

            await _run(conn)

            landing = await _node(conn, "project", scopes.personal_project["id"])
            vfolder = await _node(conn, "vfolder", vfolder_id)
            assert (await _owners(conn, vfolder))[landing] is True
            assert await _caps(conn, landing, vfolder) == {1, 2}

    async def test_a_share_to_a_project_without_a_cap_lends_every_bit(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            recipient = ("project", scopes.personal_project["id"])
            vfolder_id = await self._share(conn, rows, scopes, recipient, None)

            await _run(conn)

            landing = await _node(conn, "project", scopes.personal_project["id"])
            vfolder = await _node(conn, "vfolder", vfolder_id)
            assert (await _owners(conn, vfolder))[landing] is True
            assert await _caps(conn, landing, vfolder) == _ALL_BITS

    async def test_a_share_into_the_owning_project_leaves_it_own(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            vfolder_id = await self._share(conn, rows, scopes, ("project", scopes.project["id"]), 1)

            await _run(conn)

            project = await _node(conn, "project", scopes.project["id"])
            vfolder = await _node(conn, "vfolder", vfolder_id)
            assert (await _owners(conn, vfolder))[project] is False
            assert await _caps(conn, project, vfolder) == set()


class TestRoles:
    async def _preset(
        self, rows: _Rows, scope_type: str, auto_assign: bool, **values: Any
    ) -> sa.RowMapping:
        preset = await rows.insert(
            "role_presets",
            scope_type=scope_type,
            auto_assign=auto_assign,
            deleted=False,
            role_name_template=None,
            **values,
        )
        await rows.insert(
            "role_permission_presets",
            role_preset_id=preset["id"],
            entity_type="vfolder",
            permission=1,
        )
        return preset

    async def _role_of(
        self, conn: AsyncConnection, preset_id: uuid.UUID, scope_id: uuid.UUID
    ) -> sa.RowMapping:
        role = (
            (
                await conn.execute(
                    sa.text("SELECT * FROM roles WHERE role_preset_id = :p AND scope_id = :s"),
                    {"p": preset_id, "s": scope_id},
                )
            )
            .mappings()
            .one_or_none()
        )
        assert role is not None
        return role

    async def _granted(self, conn: AsyncConnection, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        return bool(
            await conn.scalar(
                sa.text("SELECT count(*) FROM user_roles WHERE user_id = :u AND role_id = :r"),
                {"u": user_id, "r": role_id},
            )
        )

    async def test_each_scope_gets_the_role_of_its_preset_with_the_permissions(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            preset = await self._preset(rows, "project", False, name="project_viewer")

            await _run(conn)

            for project_id in (scopes.project["id"], scopes.personal_project["id"]):
                role = await self._role_of(conn, preset["id"], project_id)
                assert role["name"] == f"project_viewer-{str(project_id)[:8]}"
                role_node = await _node(conn, "role", role["id"])
                project = await _node(conn, "project", project_id)
                assert (await _owners(conn, role_node))[project] is False
                assert (await _governors(conn, role_node))[project] is None
                assert await conn.scalar(
                    sa.text(
                        "SELECT count(*) FROM permissions WHERE role_id = :r"
                        " AND entity_type = 'vfolder' AND permission = 1"
                    ),
                    {"r": role["id"]},
                )

    async def test_a_deleted_preset_makes_no_role(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            await _scopes(rows)
            preset = await self._preset(rows, "project", False)
            await conn.execute(
                sa.text("UPDATE role_presets SET deleted = TRUE WHERE id = :p"), {"p": preset["id"]}
            )

            await _run(conn)

            assert not await conn.scalar(
                sa.text("SELECT count(*) FROM roles WHERE role_preset_id = :p"), {"p": preset["id"]}
            )

    async def test_a_user_holds_the_auto_assign_roles_of_itself_its_domain_and_its_projects(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            presets = {
                scope_type: await self._preset(rows, scope_type, True)
                for scope_type in ("user", "domain", "project")
            }

            await _run(conn)

            user_id = scopes.user["uuid"]
            for scope_type, scope_id in (
                ("user", user_id),
                ("domain", scopes.domain["id"]),
                ("project", scopes.project["id"]),
                ("project", scopes.personal_project["id"]),
            ):
                role = await self._role_of(conn, presets[scope_type]["id"], scope_id)
                assert await self._granted(conn, user_id, role["id"])

    async def test_a_project_creator_on_its_roster_holds_its_admin_role(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            admin_preset_id = uuid.UUID(PROJECT_ADMIN_PRESET_ID)
            await self._preset(rows, "project", False, id=admin_preset_id)

            await _run(conn)

            created = await self._role_of(conn, admin_preset_id, scopes.personal_project["id"])
            assert await self._granted(conn, scopes.user["uuid"], created["id"])
            joined = await self._role_of(conn, admin_preset_id, scopes.project["id"])
            assert not await self._granted(conn, scopes.user["uuid"], joined["id"])


class TestRerun:
    async def test_running_twice_changes_nothing(self, db: ExtendedAsyncSAEngine) -> None:
        tables = (
            "virtual_entities",
            "entity_memberships",
            "entity_membership_caps",
            "scope_bindings",
            "roles",
            "permissions",
            "user_roles",
        )
        async with db.begin() as conn:
            rows = _Rows(conn)
            scopes = await _scopes(rows)
            for created_in_case in _CREATED_IN_CASES.values():
                await created_in_case(conn, rows, scopes)
            for relation_case in _RELATION_CASES.values():
                await relation_case(conn, rows, scopes)

            await _run(conn)
            counts = [await conn.scalar(sa.text(f"SELECT count(*) FROM {t}")) for t in tables]
            await _run(conn)
            again = [await conn.scalar(sa.text(f"SELECT count(*) FROM {t}")) for t in tables]

            assert again == counts
