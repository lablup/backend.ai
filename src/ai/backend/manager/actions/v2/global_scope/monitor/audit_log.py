from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor.base import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.result import GlobalActionProcessResult
from ai.backend.manager.repositories.audit_log.creators import GlobalAuditLogCreatorSpec
from ai.backend.manager.repositories.audit_log.repository import AuditLogRepository
from ai.backend.manager.repositories.base import Creator

__all__ = ("GlobalActionAuditLogMonitor",)


class GlobalActionAuditLogMonitor(GlobalActionMonitor):
    """Persists one audit-log row per global action run.

    Every target column stays NULL; ``action_kind='global'`` is what marks the row
    as a system-wide operation.
    """

    _repository: AuditLogRepository

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    @override
    async def prepare(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseGlobalAction, result: GlobalActionProcessResult) -> None:
        trigger = triggered_user()
        acting = current_user()
        meta = result.meta
        creator = Creator(
            spec=GlobalAuditLogCreatorSpec(
                action_id=meta.action_id,
                entity_type=action.entity_type(),
                operation=action.operation_type(),
                created_at=meta.started_at,
                description=meta.description,
                status=meta.status,
                request_id=current_request_id() or BLANK_ID,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                duration=meta.duration,
            )
        )
        await self._repository.create(creator)
