"""Scoped idle-checker-assignment search action and its searchable targets."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerAssignmentOperationScope


@dataclass(frozen=True)
class IdleCheckerAssignmentScopeTarget(SearchableActionTarget):
    """Scope item keyed by a bound scope ``(scope_type, scope_id)``."""

    scope_type: ScopeType
    scope_id: uuid.UUID

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType(self.scope_type.value),
            element_id=str(self.scope_id),
        )

    @override
    def to_search_scope(self) -> OperationScope:
        return IdleCheckerAssignmentOperationScope(
            scope_type=self.scope_type,
            scope_id=self.scope_id,
        )


@dataclass
class ScopedSearchIdleCheckerAssignmentsAction(BaseBulkAction[SearchableActionTarget]):
    items: list[SearchableActionTarget]
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IDLE_CHECKER_ASSIGNMENT

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def targets(self) -> Sequence[SearchableActionTarget]:
        return list(self.items)


@dataclass
class ScopedSearchIdleCheckerAssignmentsActionResult(BaseBulkActionResult):
    data: list[IdleCheckerAssignmentData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    queried_refs: list[RBACElementRef]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return list(self.queried_refs)
