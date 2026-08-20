"""Audit-log search over the entities it reads the records of."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.searchers import AuditLogSearcher
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.audit_log.types import (
    EntityAuditLogOperationScope,
    TriggeredByAuditLogOperationScope,
)


class AuditLogScopeItem(ABC):
    """One entity a scoped audit-log read runs within.

    Answers the two axes separately: which entity authorizes the read, and which rows it
    selects. They differ here — an actor's records are authorized at that user but
    matched on a different column than an entity's own.
    """

    @abstractmethod
    def owner_id(self) -> EntityIdentifier:
        """The entity the read is answered for."""
        raise NotImplementedError

    @abstractmethod
    def operation_scope(self) -> OperationScope:
        """The rows the read is restricted to."""
        raise NotImplementedError


@dataclass(frozen=True)
class EntityAuditLogScopeItem(AuditLogScopeItem):
    """The records tagged with one entity — a session, a deployment, a user."""

    owner: EntityIdentifier

    @override
    def owner_id(self) -> EntityIdentifier:
        return self.owner

    @override
    def operation_scope(self) -> OperationScope:
        return EntityAuditLogOperationScope(
            entity_type=self.owner.entity_type(), entity_id=str(self.owner)
        )


@dataclass(frozen=True)
class TriggeredByAuditLogScopeItem(AuditLogScopeItem):
    """The records one user triggered, whoever they were about."""

    user_id: UserID

    @override
    def owner_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return TriggeredByAuditLogOperationScope(triggered_by=str(self.user_id))


@dataclass
class ScopedSearchAuditLogsAction(BulkScopedSearchOpsAction[AuditLogRow, AuditLogData]):
    """Page through the records of the entities named, combined with OR.

    Every entity is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[AuditLogScopeItem]
    searcher: AuditLogSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_audit_logs"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [item.owner_id() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> AuditLogSearcher:
        return self.searcher
