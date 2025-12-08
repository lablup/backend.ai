from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult

from .base import AgentAction


@dataclass
class LoadContainerCountsAction(AgentAction):
    """Action to load container counts."""

    agent_ids: list[AgentId]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "load_container_counts"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class LoadContainerCountsActionResult(BaseActionResult):
    """Result of loading container counts."""

    container_counts: Mapping[AgentId, int]

    @override
    def entity_id(self) -> Optional[str]:
        return None
