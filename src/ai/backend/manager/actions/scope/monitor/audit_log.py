from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.scope.base import BaseScopeAction
from ai.backend.manager.actions.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.scope.result import ScopeActionProcessResult
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.repositories.audit_log.creators import AuditLogCreatorSpec
from ai.backend.manager.repositories.audit_log.repository import AuditLogRepository
from ai.backend.manager.repositories.base import Creator

__all__ = ("ScopeActionAuditLogMonitor",)


class ScopeActionAuditLogMonitor(ScopeActionMonitor):
    """Persists one audit-log row per target scope of a scope action run.

    A scope action has no single entity id; each row records the target scope as
    ``"{scope_type}:{scope_id}"`` in the ``entity_id`` column, and the rows share
    the ``action_id``, which ties them back to the same run.
    """

    _repository: AuditLogRepository

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    @override
    async def prepare(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseScopeAction, result: ScopeActionProcessResult) -> None:
        trigger = triggered_user()
        acting = current_user()
        meta = result.meta
        request_id = current_request_id() or BLANK_ID
        for scope in meta.scope_targets:
            creator = Creator(
                spec=AuditLogCreatorSpec(
                    action_id=meta.action_id,
                    entity_type=action.entity_type(),
                    operation=action.operation_type(),
                    created_at=meta.started_at,
                    description=meta.description,
                    status=meta.status,
                    entity_id=f"{scope.scope_type}:{scope.scope_id}",
                    request_id=request_id,
                    triggered_by=str(trigger.user_id) if trigger else None,
                    acted_as=acting.user_id if acting else None,
                    duration=meta.duration,
                )
            )
            await self._repository.create(creator)
