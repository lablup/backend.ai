"""Scoped audit-log search action and the scopes it reads within."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.audit_log import AUDIT_LOG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.audit_log.searchers import AuditLogSearcher
from ai.backend.manager.repositories.audit_log.types import (
    EntityAuditLogOperationScope,
    TriggeredByAuditLogOperationScope,
)


class AuditLogScopeItem(ABC):
    """One scope a scoped audit-log read runs within.

    Answers the two axes separately: which scope authorizes the read, and which rows it
    selects. They differ here — an actor's records are authorized at that user but
    matched on a different column than an entity's own.
    """

    @abstractmethod
    def scope_ref(self) -> ScopeRef:
        """The scope the read is answered for."""
        raise NotImplementedError

    @abstractmethod
    def operation_scope(self) -> OperationScope:
        """The rows the read is restricted to."""
        raise NotImplementedError


@dataclass(frozen=True)
class EntityAuditLogScopeItem(AuditLogScopeItem):
    """The records tagged with one entity — a session, a deployment, a user."""

    entity_type: RBACElementType
    entity_id: uuid.UUID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(
            scope_type=ScopeType(EntityType(self.entity_type.value)), scope_id=self.entity_id
        )

    @override
    def operation_scope(self) -> OperationScope:
        return EntityAuditLogOperationScope(
            entity_type=self.entity_type, entity_id=str(self.entity_id)
        )


@dataclass(frozen=True)
class TriggeredByAuditLogScopeItem(AuditLogScopeItem):
    """The records one user triggered, whoever they were about."""

    user_id: uuid.UUID

    @override
    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id)

    @override
    def operation_scope(self) -> OperationScope:
        return TriggeredByAuditLogOperationScope(triggered_by=str(self.user_id))


@dataclass
class ScopedSearchAuditLogsAction(OperationScopeOpsAction[AuditLogRow, AuditLogData]):
    """Page through the records of the scopes named, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[AuditLogScopeItem]
    searcher: AuditLogSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AUDIT_LOG_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_audit_logs"

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return [item.scope_ref() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> AuditLogSearcher:
        return self.searcher
