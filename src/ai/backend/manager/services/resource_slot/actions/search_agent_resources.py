from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass(frozen=True)
class GlobalSearchAgentResourcesAction(BaseGlobalAction):
    """Page through the slot amounts recorded across the installation."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AGENT_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_agent_resources"


@dataclass(frozen=True)
class GlobalSearchAgentResourcesResult:
    items: list[AgentResourceData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
