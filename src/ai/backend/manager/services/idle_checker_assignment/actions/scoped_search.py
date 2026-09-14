"""Scoped idle-checker-assignment search."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.idle_checker import IdleCheckerEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.models.idle_checker.scopes import IdleCheckerAssignmentOperationScope
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerAssignmentSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass(frozen=True)
class ScopedSearchIdleCheckerAssignmentsAction(BaseScopeAction):
    """Page through the bindings hanging on the named scopes, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    scopes: Sequence[EntityIdentifier]
    searcher: IdleCheckerAssignmentSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return IdleCheckerEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_idle_checker_assignments"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [scope for scope in self.scopes]

    def operation_scopes(self) -> Sequence[OperationScope]:
        return [IdleCheckerAssignmentOperationScope(scope=scope) for scope in self.scopes]


@dataclass(frozen=True)
class ScopedSearchIdleCheckerAssignmentsActionResult(BaseScopeActionResult):
    """A page of bindings. What the read reached is the checkers the bindings link."""

    items: list[IdleCheckerAssignmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [item.idle_checker_id for item in self.items]
