from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.models.agent.row import AgentRow


@dataclass(frozen=True)
class SearchAgentsAction(GlobalSearcherOpsAction[AgentRow, AgentData]):
    """A page read across every agent, behind the SUPERADMIN gate.

    The admin search surfaces are the only callers: the agent DataLoaders name
    their entities and are checked per entity through the bulk get.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AgentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_agents"
