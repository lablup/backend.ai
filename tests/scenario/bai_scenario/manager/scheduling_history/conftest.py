"""The scheduling history adapter, assembled for one row.

Nothing outside the database is reached: every read goes through the history
repository and the owner lookups.
"""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    GroupMeta,
    ProcessorDependencies,
)
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.scheduling_history.adapter import (
    SchedulingHistoryAdapter,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_slot.repository import ResourceSlotRepository
from ai.backend.manager.repositories.scheduling_history.repository import (
    SchedulingHistoryRepository,
)
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.resource_slot.service import ResourceSlotService
from ai.backend.manager.services.scheduling_history.processors import (
    SchedulingHistoryProcessors,
)
from ai.backend.manager.services.scheduling_history.service import SchedulingHistoryService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> SchedulingHistoryAdapter:
    provider = V2DBOpsProvider(engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(provider),
        )
    )
    session_groups = registry.concern(ConcernMeta(Concern.SESSION))
    deployment_groups = registry.concern(ConcernMeta(Concern.DEPLOYMENT))
    return SchedulingHistoryAdapter(
        SchedulingHistoryProcessors(
            session_groups.group(GroupMeta(SessionEntityType())),
            deployment_groups.group(GroupMeta(DeploymentEntityType())),
            deployment_groups.group(GroupMeta(DeploymentEntityType())),
            SchedulingHistoryService(SchedulingHistoryRepository(engine, provider)),
        ),
        ResourceSlotProcessors(
            registry.group(GroupMeta(ResourceSlotTypeEntityType())),
            registry.group(GroupMeta(SessionEntityType())),
            registry.group(GroupMeta(AgentEntityType())),
            ResourceSlotService(ResourceSlotRepository(engine)),
        ),
    )
