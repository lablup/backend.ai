from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.scopes import KernelHistoryTarget
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchKernelScopedHistoryAction(BaseScopeAction):
    """Action to search kernel scheduling history under one scope item."""

    # TODO: Widen to a list of targets once this becomes a bulk action; the scope
    # input already accepts several items and means them to be OR'd, but a
    # BaseScopeAction authorizes exactly one target.
    target: KernelHistoryTarget
    querier: BatchQuerier

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (self.target.scope_id(),)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_kernel_scoped_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchKernelScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching kernel scheduling history under one scope item."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()

    items: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    target: KernelHistoryTarget
