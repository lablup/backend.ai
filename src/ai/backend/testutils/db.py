from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import AsyncGenerator, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any, Protocol, cast

from sqlalchemy import Table, text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql.ddl import SchemaGenerator
from sqlalchemy.sql.schema import ForeignKeyConstraint

# Importing these Row classes registers them on the shared SQLAlchemy declarative
# registry so that relationship() targets resolve during mapper configuration, and
# lets the TABLE_DEPENDENCY map below reference them. The map (generated from the
# relationship + foreign-key graph) closes a row's transitive dependencies so
# with_tables() can create them together.
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group.row import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.network.row import NetworkRow
from ai.backend.manager.models.notification.row import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.prometheus_query_preset.row import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset_category.row import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    PresetResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_usage_history.row import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.scaling_group.row import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.vfolder.row import (
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)


class HasTable(Protocol):
    """Protocol for SQLAlchemy ORM model classes with __table__ attribute."""

    __table__: Table


# Type alias for items that can be passed to with_tables
type TableOrORM = Table | type[HasTable]


def _make_subset_schema_generator(table_names: frozenset[str]) -> type[SchemaGenerator]:
    """
    Build a ``SchemaGenerator`` that skips deferred (``use_alter``) foreign keys
    pointing outside the requested table subset.

    ``MetaData.create_all(tables=...)`` still emits the deferred
    ``ALTER TABLE ... ADD CONSTRAINT`` for ``use_alter`` foreign keys even when the
    referenced table is absent from the subset, which fails with ``UndefinedTableError``
    (e.g. ``sessions.replica_id -> routings`` when a test loads ``sessions`` but not
    ``routings``). Suppressing only that standalone ``ALTER`` keeps selective table
    loading working without forcing every caller to pull in cycle-breaking tables.

    Inline foreign keys are rendered by the ``CREATE TABLE`` compiler, not this visitor,
    so they are unaffected; only standalone ``use_alter`` constraints flow through here.
    """

    class _SubsetSchemaGenerator(SchemaGenerator):
        def visit_foreign_key_constraint(self, constraint: ForeignKeyConstraint) -> None:
            elements = constraint.elements
            if elements:
                referred_table = elements[0].target_fullname.rsplit(".", 1)[0]
                if referred_table not in table_names:
                    return
            emit = cast(
                "Callable[[ForeignKeyConstraint], None]",
                super().visit_foreign_key_constraint,
            )
            emit(constraint)

    return _SubsetSchemaGenerator


def _create_tables_sync(conn: Any, tables: list[Table]) -> None:
    """
    Sync function to create tables, reusing ``create_all`` machinery (checkfirst,
    enum types, indexes) via a custom ``SchemaGenerator``.

    This handles circular FK dependencies via ``use_alter`` while dropping deferred
    foreign keys that reference tables outside the requested subset, so each test file
    can create only the tables it needs.
    """
    if not tables:
        return
    metadata = tables[0].metadata
    generator = _make_subset_schema_generator(frozenset(t.name for t in tables))
    conn._run_ddl_visitor(generator, metadata, checkfirst=True, tables=tables)


def _to_table(item: TableOrORM) -> Table:
    """Convert ORM class or Table to Table."""
    if isinstance(item, Table):
        return item
    return item.__table__


TABLE_DEPENDENCY: Mapping[TableOrORM, list[TableOrORM]] = {
    AgentResourceRow: [AgentRow, ResourceSlotTypeRow],
    AgentRow: [ScalingGroupRow],
    AssocGroupUserRow: [GroupRow, UserRow],
    AssociationContainerRegistriesGroupsRow: [],
    AssociationScopesEntitiesRow: [],
    ContainerRegistryRow: [],
    DeploymentAutoScalingPolicyRow: [],
    DeploymentPolicyRow: [EndpointRow],
    DeploymentRevisionPresetRow: [],
    DeploymentRevisionResourceSlotRow: [DeploymentRevisionRow, ResourceSlotTypeRow],
    DeploymentRevisionRow: [DeploymentRevisionPresetRow, ImageRow, RuntimeVariantRow, VFolderRow],
    DomainFairShareRow: [],
    DomainRow: [],
    DomainUsageBucketRow: [],
    EndpointAutoScalingRuleRow: [EndpointRow, PrometheusQueryPresetRow],
    EndpointRow: [DomainRow, GroupRow, ScalingGroupRow],
    EndpointTokenRow: [DomainRow, GroupRow],
    GroupRow: [DomainRow, ProjectResourcePolicyRow],
    ImageAliasRow: [ImageRow],
    ImageRow: [ContainerRegistryRow],
    KernelRow: [AgentRow, DomainRow, GroupRow, ImageRow, ScalingGroupRow, SessionRow],
    KernelUsageRecordRow: [],
    KeyPairResourcePolicyRow: [],
    KeyPairRow: [KeyPairResourcePolicyRow, UserRow],
    NetworkRow: [],
    NotificationChannelRow: [],
    NotificationRuleRow: [],
    ObjectPermissionRow: [],
    PresetResourceSlotRow: [DeploymentRevisionPresetRow, ResourceSlotTypeRow],
    ProjectFairShareRow: [],
    ProjectResourcePolicyRow: [],
    ProjectUsageBucketRow: [],
    PrometheusQueryPresetCategoryRow: [],
    PrometheusQueryPresetRow: [PrometheusQueryPresetCategoryRow],
    ReplicaGroupRow: [EndpointRow],
    ResourcePresetRow: [],
    ResourceSlotTypeRow: [],
    RoleRow: [],
    RoutingRow: [DomainRow, EndpointRow, GroupRow, ReplicaGroupRow, SessionRow, UserRow],
    RuntimeVariantPresetRow: [],
    RuntimeVariantRow: [],
    ScalingGroupForDomainRow: [DomainRow, ScalingGroupRow],
    ScalingGroupForKeypairsRow: [KeyPairRow, ScalingGroupRow],
    ScalingGroupForProjectRow: [GroupRow, ScalingGroupRow],
    ScalingGroupRow: [],
    SessionRow: [DomainRow, GroupRow, RoutingRow, ScalingGroupRow],
    UserFairShareRow: [],
    UserResourcePolicyRow: [],
    UserRoleRow: [RoleRow, UserRow],
    UserRow: [DomainRow, KeyPairRow, UserResourcePolicyRow],
    UserUsageBucketRow: [],
    VFolderInvitationRow: [VFolderRow],
    VFolderPermissionRow: [UserRow, VFolderRow],
    VFolderRow: [],
}


@asynccontextmanager
async def with_tables(
    engine: AsyncEngine,
    orms: Sequence[TableOrORM],
) -> AsyncGenerator[None, None]:
    """
    Create specified tables on enter, TRUNCATE CASCADE on exit.

    ORM classes should be ordered by FK dependencies (parents first).
    This context manager is designed for selective table loading in tests,
    allowing each test file to create only the tables it needs.

    Args:
        engine: SQLAlchemy async engine
        orms: Sequence of SQLAlchemy ORM model classes or Table objects
              (ordered by FK dependencies)

    Example:
        async def test_something(database_connection):
            async with with_tables(database_connection, [DomainRow, UserRow, GroupRow]):
                ...

        # With association tables:
        async with with_tables(database_connection, [
            DomainRow,
            ScalingGroupRow,
            sgroups_for_domains,  # raw Table object
        ]):
            ...
    """

    normalized_dependency: defaultdict[Table, set[Table]] = defaultdict(set)
    for table, deps in TABLE_DEPENDENCY.items():
        normalized_dependency[_to_table(table)] |= {_to_table(dep) for dep in deps}
    resolved: set[Table] = set()
    tables = deque([_to_table(orm) for orm in orms])
    while tables:
        table = tables.popleft()
        if table in resolved:
            continue
        resolved.add(table)
        dependencies = normalized_dependency.get(table, set())
        for dep in dependencies:
            dep_table = _to_table(dep)
            if dep_table not in resolved:
                tables.append(dep_table)

    # Create required PostgreSQL extensions and tables
    async with engine.begin() as conn:
        # Create uuid-ossp extension for uuid_generate_v4()
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(_create_tables_sync, list(resolved))

    try:
        yield
    finally:
        # Cleanup via TRUNCATE CASCADE
        async with engine.begin() as conn:
            table_names = ", ".join(f'"{t.name}"' for t in resolved)
            await conn.execute(text(f"TRUNCATE {table_names} CASCADE"))
