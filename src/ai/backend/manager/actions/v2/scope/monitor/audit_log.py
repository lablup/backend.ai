from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.result import ScopeActionProcessResult
from ai.backend.manager.repositories.audit_log.creators import (
    AuditLogScopeCreatorSpec,
    ScopeAuditLogCreatorSpec,
)
from ai.backend.manager.repositories.audit_log.repository import AuditLogRepository
from ai.backend.manager.repositories.base import BulkCreator

__all__ = ("ScopeActionAuditLogMonitor",)


class ScopeActionAuditLogMonitor(ScopeActionMonitor):
    """Persists one audit-log row per entity a scope action affected.

    Rows are keyed on the entity, not the scope, so a run over several scopes is not
    mistaken for several runs. The scopes the request covered are attached to every
    row via ``audit_log_scopes``. A run that affected nothing still leaves one row.
    """

    _repository: AuditLogRepository

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    @override
    async def prepare(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseScopeAction, result: ScopeActionProcessResult) -> None:
        meta = result.meta
        specs = [self._build_spec(action, result, entity_id) for entity_id in meta.entity_ids]
        if not specs:
            # Nothing was touched, but the run still has to leave a trace.
            specs = [self._build_spec(action, result, None)]
        await self._repository.bulk_create_with_scopes(
            BulkCreator(specs=specs),
            [
                AuditLogScopeCreatorSpec(scope_type=str(s.scope_type), scope_id=s.scope_id)
                for s in meta.scope_targets
            ],
        )

    def _build_spec(
        self,
        action: BaseScopeAction,
        result: ScopeActionProcessResult,
        entity_id: EntityID | None,
    ) -> ScopeAuditLogCreatorSpec:
        trigger = triggered_user()
        acting = current_user()
        meta = result.meta
        return ScopeAuditLogCreatorSpec(
            action_id=meta.action_id,
            entity_type=action.entity_type(),
            operation=action.operation_type(),
            created_at=meta.started_at,
            description=meta.description,
            status=meta.status,
            entity_id=entity_id,
            request_id=current_request_id() or BLANK_ID,
            triggered_by=str(trigger.user_id) if trigger else None,
            acted_as=acting.user_id if acting else None,
            duration=meta.duration,
        )
