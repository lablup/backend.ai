from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import BulkActionProcessResult
from ai.backend.manager.repositories.audit_log.creators import BulkAuditLogCreatorSpec
from ai.backend.manager.repositories.audit_log.repository import AuditLogRepository
from ai.backend.manager.repositories.base import BulkCreator

__all__ = ("BulkActionAuditLogMonitor",)


class BulkActionAuditLogMonitor(BulkActionMonitor):
    """Persists one audit-log row per target entity of a bulk action run.

    Audit-log rows are tagged with a single ``(entity_type, entity_id)`` pair, so a
    bulk run fans out into one row per target; the rows share the ``action_id``,
    which ties them back to the same run. The rows are inserted in a single bulk
    create rather than one round-trip per target.
    """

    _repository: AuditLogRepository
    _policy: AuditLogPolicy

    def __init__(self, repository: AuditLogRepository, policy: AuditLogPolicy) -> None:
        self._repository = repository
        self._policy = policy

    @override
    async def prepare(self, action: BaseBulkAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseBulkAction, result: BulkActionProcessResult) -> None:
        trigger = triggered_user()
        acting = current_user()
        meta = result.meta
        request_id = current_request_id() or BLANK_ID
        spec = action.spec()
        bulk_creator = BulkCreator(
            specs=[
                BulkAuditLogCreatorSpec(
                    action_id=meta.action_id,
                    entity_type=action.entity_type(),
                    operation=action.operation_type(),
                    created_at=meta.started_at,
                    description=entity_result.description,
                    status=entity_result.status,
                    entity_id=entity_result.entity_id,
                    request_id=request_id,
                    triggered_by=str(trigger.user_id) if trigger else None,
                    acted_as=acting.user_id if acting else None,
                    duration=meta.duration,
                )
                for entity_result in meta.entity_results
                if self._policy.should_record(spec, entity_result.status)
            ]
        )
        await self._repository.bulk_create(bulk_creator)
