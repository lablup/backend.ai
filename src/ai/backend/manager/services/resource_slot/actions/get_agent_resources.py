from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_slot.types import AgentResourceData

from .base import ResourceSlotAction


@dataclass
class GetAgentResourcesAction(ResourceSlotAction):
    agent_id: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.AGENT_RESOURCE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.agent_id


@dataclass
class GetAgentResourcesResult(BaseActionResult):
    items: list[AgentResourceData]

    @override
    def entity_id(self) -> str | None:
        return None
