from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.agent.actions.base import AgentAction
from ai.backend.manager.services.agent.types import ConflictingSessionCleanupPolicy


@dataclass
class UpdateAgentResourceGroupAction(AgentAction):
    agent_id: AgentId
    # Target resource group id (already resolved by the caller).
    resource_group_id: ResourceGroupID
    # How to handle sessions still running on the agent under the old group.
    policy: ConflictingSessionCleanupPolicy
    force: bool

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateAgentResourceGroupActionResult(BaseActionResult):
    agent_id: AgentId
    resource_group_id: ResourceGroupID
    conflicting_session_ids: list[SessionId]
    terminating_session_ids: list[SessionId]

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)
