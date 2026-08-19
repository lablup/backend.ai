from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.replica_group_history import (
    REPLICA_GROUP_HISTORY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class GlobalSearchReplicaGroupHistoryAction(BaseGlobalAction):
    """Action to search replica-group scheduling history across every scope."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return REPLICA_GROUP_HISTORY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_replica_group_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class GlobalSearchReplicaGroupHistoryActionResult:
    """Result of searching replica-group scheduling history."""

    items: list[ReplicaGroupHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
