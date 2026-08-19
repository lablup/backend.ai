from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.resource_slot.types import AgentResourceData


@dataclass(frozen=True)
class GetAgentResourceBySlotAction(BaseSingleEntityAction):
    """Read one slot's amount on one agent.

    The row belongs to the agent, so the agent answers for the read.
    """

    agent_uuid: AgentUUID
    agent_id: str
    slot_name: str

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.agent_uuid

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_agent_resource_by_slot"


@dataclass(frozen=True)
class GetAgentResourceBySlotResult:
    item: AgentResourceData
