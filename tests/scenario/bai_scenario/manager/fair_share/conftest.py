"""The fair share adapter, assembled for one row.

Fair share rows are dangling fields of the resource group concern, wired the way the
production processor factory wires them.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.fair_share import (
    DomainFairShareFieldType,
    ProjectFairShareFieldType,
    UserFairShareFieldType,
)
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
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
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.repositories.fair_share.repository import FairShareRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.fair_share.service import FairShareService
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> FairShareAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    resource_group_groups = registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    return FairShareAdapter(
        FairShareProcessors(
            resource_group_groups.dangling_field_group(
                FieldGroupMeta(DomainFairShareFieldType()), DomainFairShareData
            ),
            resource_group_groups.dangling_field_group(
                FieldGroupMeta(ProjectFairShareFieldType()), ProjectFairShareData
            ),
            resource_group_groups.dangling_field_group(
                FieldGroupMeta(UserFairShareFieldType()), UserFairShareData
            ),
            FairShareService(FairShareRepository(engine, provider)),
        ),
        ResourceGroupProcessors(
            registry.group(GroupMeta(ResourceGroupEntityType())),
            ResourceGroupService(ResourceGroupRepository(engine, provider)),
        ),
    )
