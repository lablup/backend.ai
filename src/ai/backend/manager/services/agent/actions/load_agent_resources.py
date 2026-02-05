from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.resource.types import AgentResourceData
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult

from .base import AgentAction


@dataclass
class LoadAgentResourcesAction(AgentAction):
    """Action to load agent resource information."""

    agent_ids: Sequence[AgentId]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class LoadAgentResourcesActionResult(BaseActionResult):
    """Result of loading agent resources.

    agent_resources is a mapping from agent_id to AgentResourceData.
    """

    agent_resources: Mapping[AgentId, AgentResourceData]

    @override
    def entity_id(self) -> str | None:
        return None
