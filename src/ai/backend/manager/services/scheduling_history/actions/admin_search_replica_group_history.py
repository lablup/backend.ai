from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.action.global_action import BaseGlobalAction
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class AdminSearchReplicaGroupHistoryAction(BaseGlobalAction):
    """Action to search replica-group scheduling history (admin API).

    System-wide and unscoped: authorization is the SUPERADMIN role gate rather
    than RBAC scope resolution, so this runs through ``GlobalActionProcessor``.
    The scoped counterpart stays on the RBAC path.
    """

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.REPLICA_GROUP_HISTORY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class AdminSearchReplicaGroupHistoryActionResult(BaseActionResult):
    """Result of searching replica-group scheduling history."""

    items: list[ReplicaGroupHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
