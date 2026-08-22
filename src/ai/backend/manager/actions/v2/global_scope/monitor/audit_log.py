from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.common.data.entity.types import GLOBAL_ENTITY_TYPE
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor.base import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.result import GlobalActionProcessResult
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.creators import GlobalAuditLogCreator
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = ("GlobalActionAuditLogMonitor",)


class GlobalActionAuditLogMonitor(GlobalActionMonitor):
    """Persists one audit-log row per global action run.

    Every target column stays NULL; ``action_kind='global'`` is what marks the row
    as a system-wide operation.
    """

    _repository: OpsRepository[AuditLogData]
    _policy: AuditLogPolicy

    def __init__(self, repository: OpsRepository[AuditLogData], policy: AuditLogPolicy) -> None:
        self._repository = repository
        self._policy = policy

    @override
    async def prepare(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseGlobalAction, result: GlobalActionProcessResult) -> None:
        meta = result.meta
        if not self._policy.should_record(action.operation_type(), meta.status):
            return
        trigger = triggered_user()
        acting = current_user()
        creator = GlobalAuditLogCreator(
            action_id=meta.action_id,
            operation=action.operation_type(),
            action_name=action.action_name(),
            created_at=meta.started_at,
            description=meta.description,
            status=meta.status,
            request_id=current_request_id() or BLANK_ID,
            triggered_by=str(trigger.user_id) if trigger else None,
            acted_as=acting.user_id if acting else None,
            duration=meta.duration,
        )
        await self._repository.create_dangling_field(GLOBAL_ENTITY_TYPE, creator)
