from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.v2.single_entity.trigger import (
    SingleEntityActionTriggerMeta,
)
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.creators import (
    SingleEntityAuditLogCreator,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = ("SingleEntityActionAuditLogMonitor",)


class SingleEntityActionAuditLogMonitor(SingleEntityActionMonitor):
    """Persists one audit-log row per single-entity action run.

    ``entity_id`` is always recorded because :class:`BaseSingleEntityAction`
    operates on an identified entity.
    """

    _repository: OpsRepository[AuditLogData]
    _policy: AuditLogPolicy

    def __init__(self, repository: OpsRepository[AuditLogData], policy: AuditLogPolicy) -> None:
        self._repository = repository
        self._policy = policy

    @override
    async def prepare(self, meta: SingleEntityActionTriggerMeta) -> None:
        pass

    @override
    async def done(
        self, meta: SingleEntityActionTriggerMeta, result: SingleEntityActionProcessResult
    ) -> None:
        if not self._policy.should_record(meta.operation_type, result.meta.status):
            return
        trigger = triggered_user()
        acting = current_user()
        creator = SingleEntityAuditLogCreator(
            action_id=meta.action_id,
            entity_type=meta.entity.entity_type(),
            operation=meta.operation_type,
            action_name=meta.action_name,
            created_at=meta.started_at,
            description=result.meta.description,
            status=result.meta.status,
            entity_id=meta.entity,
            request_id=current_request_id() or BLANK_ID,
            triggered_by=str(trigger.user_id) if trigger else None,
            acted_as=acting.user_id if acting else None,
            duration=result.meta.duration,
        )
        await self._repository.create_sidecar(creator)
