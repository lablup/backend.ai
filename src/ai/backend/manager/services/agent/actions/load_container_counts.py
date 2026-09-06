from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass(frozen=True)
class LoadContainerCountsAction(BaseGlobalAction):
    """Action to load container counts."""

    agent_ids: Sequence[AgentId]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AGENT_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_load_agent_container_counts"


@dataclass(frozen=True)
class LoadContainerCountsActionResult:
    """Result of loading container counts.

    container_counts is in the same order as the input agent_ids.
    """

    container_counts: Sequence[int]
