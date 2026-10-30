from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.models.resource_slot.row import AgentResourceRow


@dataclass(frozen=True)
class GlobalSearchAgentResourcesAction(
    GlobalSearcherOpsAction[AgentResourceRow, AgentResourceData]
):
    """Page through the slot amounts recorded across the installation."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AgentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_agent_resources"
