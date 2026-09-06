from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.agent.types import AgentDetailData
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass(frozen=True)
class SearchAgentsAction(BaseGlobalAction):
    """A page read across every agent.

    The gate belongs on SUPERADMIN -- both surfaces already declare it -- but the
    action stays public until the agent DataLoaders stop reaching for it. A
    DataLoader must name its entities and be checked per entity
    (``partial_bulk_get_ops``); reading them through this search is what forces
    the gate open. Moving the loaders needs a bulk key lookup that does not exist
    yet, so it is a change of its own.
    """

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
        return "global_search_agents"


@dataclass(frozen=True)
class SearchAgentsActionResult:
    """Result of searching agents with their permissions."""

    agents: list[AgentDetailData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
