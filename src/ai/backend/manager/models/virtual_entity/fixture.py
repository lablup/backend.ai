"""Graph nodes for the entities a fixture writes.

A fixture inserts rows straight into their table, so the node the v2 entity ops
provision alongside a created row is missing and every graph read of that entity
fails. Each table below declares the entity its rows are, and provisioning gives
every row of it a node owning and governing itself.

The declaration covers the tables the repository's fixtures load. A fixture of an
entity table left out of it writes rows with no node, the state this module exists
to prevent.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Final

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryEntityType
from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.login_client_type import LoginClientTypeEntityType
from ai.backend.common.data.entity.object_storage import ObjectStorageEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetEntityType
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryEntityType,
)
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.retention_policy import RetentionPolicyEntityType
from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantEntityType
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetEntityType
from ai.backend.common.data.entity.storage_namespace import StorageNamespaceEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.models.base import metadata
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow


@dataclass(frozen=True)
class FixtureEntitySpec:
    """The entity a table's rows are, and the column carrying the entity's id.

    The id column is not always the primary key: a table keyed by name carries it
    beside that key.
    """

    entity_type: EntityType
    id_column: str


FIXTURE_ENTITY_SPECS: Final[Mapping[str, FixtureEntitySpec]] = {
    "container_registries": FixtureEntitySpec(ContainerRegistryEntityType(), "id"),
    "domains": FixtureEntitySpec(DomainEntityType(), "id"),
    "groups": FixtureEntitySpec(ProjectEntityType(), "id"),
    "huggingface_registries": FixtureEntitySpec(ArtifactRegistryEntityType(), "id"),
    "keypair_resource_policies": FixtureEntitySpec(KeyPairResourcePolicyEntityType(), "uuid"),
    "login_client_types": FixtureEntitySpec(LoginClientTypeEntityType(), "id"),
    "object_storages": FixtureEntitySpec(ObjectStorageEntityType(), "id"),
    "project_resource_policies": FixtureEntitySpec(ProjectResourcePolicyEntityType(), "uuid"),
    "prometheus_query_preset_categories": FixtureEntitySpec(
        PrometheusQueryPresetCategoryEntityType(), "id"
    ),
    "prometheus_query_presets": FixtureEntitySpec(PrometheusQueryPresetEntityType(), "id"),
    "reservoir_registries": FixtureEntitySpec(ArtifactRegistryEntityType(), "id"),
    "resource_presets": FixtureEntitySpec(ResourcePresetEntityType(), "id"),
    "resource_slot_types": FixtureEntitySpec(ResourceSlotTypeEntityType(), "uuid"),
    "retention_policies": FixtureEntitySpec(RetentionPolicyEntityType(), "id"),
    "role_presets": FixtureEntitySpec(RolePresetEntityType(), "id"),
    "runtime_variant_presets": FixtureEntitySpec(RuntimeVariantPresetEntityType(), "id"),
    "runtime_variants": FixtureEntitySpec(RuntimeVariantEntityType(), "id"),
    "scaling_groups": FixtureEntitySpec(ResourceGroupEntityType(), "id"),
    "storage_namespace": FixtureEntitySpec(StorageNamespaceEntityType(), "id"),
    "user_resource_policies": FixtureEntitySpec(UserResourcePolicyEntityType(), "uuid"),
    "users": FixtureEntitySpec(UserEntityType(), "uuid"),
}


async def provision_fixture_entities(conn: AsyncConnection, table_names: Collection[str]) -> None:
    """Give every row of each declared table among ``table_names`` a virtual entity node
    that owns and governs it, as creating the row through the entity ops would have.

    Runs over the whole table rather than the rows just written, so a fixture leaving
    the id to the server default is covered and a second run changes nothing. A node a
    fixture wrote itself stays as it is, together with the edges naming it.
    """
    for table_name in table_names:
        spec = FIXTURE_ENTITY_SPECS.get(table_name)
        if spec is None:
            continue
        await _provision_table(conn, table_name, spec)


async def _provision_table(conn: AsyncConnection, table_name: str, spec: FixtureEntitySpec) -> None:
    table = metadata.tables[table_name]
    await conn.execute(
        pg_insert(VirtualEntityRow)
        .from_select(
            ["entity_type", "entity_id"],
            sa.select(sa.literal(str(spec.entity_type)), table.c[spec.id_column]),
        )
        .on_conflict_do_nothing(index_elements=["entity_type", "entity_id"])
    )
    nodes = sa.select(VirtualEntityRow.id).where(
        VirtualEntityRow.entity_type == spec.entity_type,
        VirtualEntityRow.entity_id.in_(sa.select(table.c[spec.id_column])),
    )
    await conn.execute(
        pg_insert(EntityMembershipRow)
        .from_select(
            ["virtual_entity_id", "member_entity_id", "capped"],
            nodes.add_columns(VirtualEntityRow.id, sa.literal(False)),
        )
        .on_conflict_do_nothing(index_elements=["virtual_entity_id", "member_entity_id"])
    )
    await conn.execute(
        pg_insert(ScopeBindingRow)
        .from_select(
            ["virtual_entity_id", "scope_entity_id"],
            nodes.add_columns(VirtualEntityRow.id),
        )
        .on_conflict_do_nothing()
    )
