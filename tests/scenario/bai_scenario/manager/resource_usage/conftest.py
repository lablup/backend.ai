"""The resource usage adapter, assembled for one row.

The buckets are read through the usage processors; the resource group lookup answers
for the group a scoped read names.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.usage_bucket import (
    DomainUsageBucketFieldType,
    ProjectUsageBucketFieldType,
    UserUsageBucketFieldType,
)
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    FieldGroupMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.resource_usage.adapter import ResourceUsageAdapter
from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService
from ai.backend.manager.services.resource_usage.processors import ResourceUsageProcessors


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ResourceUsageAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    groups = registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    return ResourceUsageAdapter(
        ResourceUsageProcessors(
            groups.dangling_field_group(
                FieldGroupMeta(DomainUsageBucketFieldType()), DomainUsageBucketData
            ),
            groups.dangling_field_group(
                FieldGroupMeta(ProjectUsageBucketFieldType()), ProjectUsageBucketData
            ),
            groups.dangling_field_group(
                FieldGroupMeta(UserUsageBucketFieldType()), UserUsageBucketData
            ),
        ),
        ResourceGroupProcessors(
            groups.group(GroupMeta(ResourceGroupEntityType())),
            ResourceGroupService(ResourceGroupRepository(engine, provider)),
        ),
    )
