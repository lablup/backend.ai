"""Scoped audit-log search action and its searchable targets."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.audit_log.types import (
    EntityAuditLogSearchScope,
    TriggeredByAuditLogSearchScope,
)
from ai.backend.manager.repositories.base import BatchQuerier, SearchScope


@dataclass(frozen=True)
class EntityAuditLogTarget(SearchableActionTarget):
    """Scope item keyed by a target entity ``(element_type, element_id)``."""

    element_type: RBACElementType
    element_id: str

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(element_type=self.element_type, element_id=self.element_id)

    @override
    def to_search_scope(self) -> SearchScope:
        return EntityAuditLogSearchScope(
            entity_type=self.element_type,
            entity_id=self.element_id,
        )


@dataclass(frozen=True)
class TriggeredByAuditLogTarget(SearchableActionTarget):
    """Scope item keyed by the actor (triggered_by) user."""

    user_id: uuid.UUID

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(self.user_id),
        )

    @override
    def to_search_scope(self) -> SearchScope:
        return TriggeredByAuditLogSearchScope(triggered_by=str(self.user_id))


@dataclass
class ScopedSearchAuditLogsAction(BaseBulkAction[SearchableActionTarget]):
    items: list[SearchableActionTarget]
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.AUDIT_LOG

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def targets(self) -> Sequence[SearchableActionTarget]:
        return list(self.items)


@dataclass
class ScopedSearchAuditLogsActionResult(BaseBulkActionResult):
    data: list[AuditLogData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    queried_refs: list[RBACElementRef]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return list(self.queried_refs)
