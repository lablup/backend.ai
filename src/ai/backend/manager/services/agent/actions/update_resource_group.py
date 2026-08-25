from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import AgentId, SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.services.agent.types import ConflictingSessionCleanupPolicy


@dataclass(frozen=True)
class UpdateAgentResourceGroupAction(BaseGlobalAction):
    agent_id: AgentId
    # Target resource group id (already resolved by the caller).
    resource_group_id: ResourceGroupID
    # How to handle sessions still running on the agent under the old group.
    policy: ConflictingSessionCleanupPolicy
    force: bool

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AGENT_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_update_agent_resource_group"


@dataclass(frozen=True)
class UpdateAgentResourceGroupActionResult:
    agent_id: AgentId
    resource_group_id: ResourceGroupID
    conflicting_session_ids: list[SessionId]
    terminating_session_ids: list[SessionId]
