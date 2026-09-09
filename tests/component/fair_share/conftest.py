from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.entity.fair_share import (
    DomainFairShareFieldType,
    ProjectFairShareFieldType,
    UserFairShareFieldType,
)
from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.data.entity.usage_bucket import (
    DomainUsageBucketFieldType,
    ProjectUsageBucketFieldType,
    UserUsageBucketFieldType,
)
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
)
from ai.backend.manager.api.rest.fair_share.handler import FairShareAPIHandler
from ai.backend.manager.api.rest.fair_share.registry import register_fair_share_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_group import resource_groups, sgroups_for_groups
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.fair_share.repository import FairShareRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.fair_share.service import FairShareService
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService
from ai.backend.manager.services.resource_usage.processors import ResourceUsageProcessors
from ai.backend.testutils.fixtures import DomainFixtureData


@pytest.fixture()
def fair_share_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> FairShareProcessors:
    service = FairShareService(FairShareRepository(database_engine))
    fair_share_groups = processor_registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    return FairShareProcessors(
        fair_share_groups.dangling_field_group(
            FieldGroupMeta(DomainFairShareFieldType()), DomainFairShareData
        ),
        fair_share_groups.dangling_field_group(
            FieldGroupMeta(ProjectFairShareFieldType()), ProjectFairShareData
        ),
        fair_share_groups.dangling_field_group(
            FieldGroupMeta(UserFairShareFieldType()), UserFairShareData
        ),
        service,
    )


@pytest.fixture()
def resource_usage_processors(
    processor_registry: ProcessorRegistry[Any],
) -> ResourceUsageProcessors:
    return ResourceUsageProcessors(
        processor_registry.dangling_field_group(
            FieldGroupMeta(DomainUsageBucketFieldType()), DomainUsageBucketData
        ),
        processor_registry.dangling_field_group(
            FieldGroupMeta(ProjectUsageBucketFieldType()), ProjectUsageBucketData
        ),
        processor_registry.dangling_field_group(
            FieldGroupMeta(UserUsageBucketFieldType()), UserUsageBucketData
        ),
    )


@pytest.fixture()
def resource_group_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> ResourceGroupProcessors:
    service = ResourceGroupService(
        ResourceGroupRepository(database_engine, V2DBOpsProvider(database_engine))
    )
    return ResourceGroupProcessors(
        processor_registry.group(GroupMeta(ResourceGroupEntityType())), service
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    fair_share_processors: FairShareProcessors,
    resource_usage_processors: ResourceUsageProcessors,
    resource_group_processors: ResourceGroupProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for fair-share-domain tests."""
    return [
        register_fair_share_routes(
            FairShareAPIHandler(
                fair_share=fair_share_processors,
                resource_usage=resource_usage_processors,
                resource_group=resource_group_processors,
            ),
            route_deps,
        ),
    ]


@pytest.fixture()
async def resource_group_name(
    db_engine: SAEngine,
    resource_group_name: ResourceGroupName,
) -> AsyncIterator[ResourceGroupName]:
    """Drop the fair-share rows a test wrote; no FK removes them with the scaling group."""
    yield resource_group_name
    async with db_engine.begin() as conn:
        sgroup_id = sa.select(resource_groups.c.id).where(
            resource_groups.c.name == resource_group_name
        )
        for row_cls in (DomainFairShareRow, ProjectFairShareRow, UserFairShareRow):
            await conn.execute(
                row_cls.__table__.delete().where(
                    row_cls.__table__.c.resource_group_id.in_(sgroup_id)
                )
            )


@pytest.fixture()
async def group_fixture(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
    resource_group_id: ResourceGroupID,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test group with scaling-group association for fair-share tests."""
    group_id = uuid.uuid4()
    group_name = f"group-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ProjectRow.__table__).values(
                id=group_id,
                name=group_name,
                description=f"Test group {group_name}",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
        virtual_entity_id = uuid.uuid4()
        await conn.execute(
            sa.insert(VirtualEntityRow.__table__).values(
                id=virtual_entity_id,
                entity_type=ScopeType.PROJECT,
                entity_id=group_id,
            )
        )
        await conn.execute(
            sa.insert(EntityMembershipRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                member_entity_id=virtual_entity_id,
                capped=False,
            )
        )
        await conn.execute(
            sa.insert(ScopeBindingRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                scope_entity_id=virtual_entity_id,
                permission_cap=None,
            )
        )
        await conn.execute(
            sa.insert(sgroups_for_groups).values(
                resource_group_id=resource_group_id,
                group=group_id,
            )
        )
    yield group_id
    async with db_engine.begin() as conn:
        await conn.execute(
            sgroups_for_groups.delete().where(sgroups_for_groups.c.group == group_id)
        )
        await conn.execute(
            VirtualEntityRow.__table__.delete().where(
                VirtualEntityRow.__table__.c.entity_type == ScopeType.PROJECT,
                VirtualEntityRow.__table__.c.entity_id == group_id,
            )
        )
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id == group_id)
        )
