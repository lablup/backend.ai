"""The resource slot adapter, assembled for the slot type rows.

The adapter also reads agent resources and kernel allocations through the agent and domain
processors. No slot type row reaches them, so they stay unwired and say so if one does.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_scenario.runner.unwired import unwired

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_slot.repository import ResourceSlotRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.resource_slot.processors import ResourceSlotProcessors
from ai.backend.manager.services.resource_slot.service import ResourceSlotService


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> ResourceSlotAdapter:
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=monitors,
            validators=validators,
            repository=OpsRepository(V2DBOpsProvider(engine)),
        )
    )
    return ResourceSlotAdapter(
        ResourceSlotProcessors(
            registry.group(GroupMeta(ResourceSlotTypeEntityType())),
            registry.group(GroupMeta(SessionEntityType())),
            registry.group(GroupMeta(AgentEntityType())),
            ResourceSlotService(ResourceSlotRepository(engine)),
        ),
        unwired(AgentProcessors, "no slot type row reads an agent"),
        unwired(DomainProcessors, "no slot type row reads a domain"),
    )
