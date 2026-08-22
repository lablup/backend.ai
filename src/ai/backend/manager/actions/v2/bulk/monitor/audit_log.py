from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import BulkActionProcessResult
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.creators import BulkAuditLogCreator
from ai.backend.manager.models.specs.creator import FieldToCreate
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = ("BulkActionAuditLogMonitor",)


class BulkActionAuditLogMonitor(BulkActionMonitor):
    """Persists one audit-log row per target entity of a bulk action run.

    Audit-log rows are tagged with a single ``(entity_type, entity_id)`` pair, so a
    bulk run fans out into one row per target; the rows share the ``action_id``,
    which ties them back to the same run. The rows are inserted in a single bulk
    create rather than one round-trip per target.
    """

    _repository: OpsRepository[AuditLogData]
    _policy: AuditLogPolicy

    def __init__(self, repository: OpsRepository[AuditLogData], policy: AuditLogPolicy) -> None:
        self._repository = repository
        self._policy = policy

    @override
    async def prepare(self, meta: BulkActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, meta: BulkActionTriggerMeta, result: BulkActionProcessResult) -> None:
        trigger = triggered_user()
        acting = current_user()
        request_id = current_request_id() or BLANK_ID
        creations = [
            FieldToCreate(
                owner_id=entity_result.entity_id,
                creator=BulkAuditLogCreator(
                    action_id=result.meta.action_id,
                    operation=meta.operation_type,
                    action_name=meta.action_name,
                    created_at=result.meta.started_at,
                    description=entity_result.description,
                    status=entity_result.status,
                    request_id=request_id,
                    triggered_by=str(trigger.user_id) if trigger else None,
                    acted_as=acting.user_id if acting else None,
                    duration=result.meta.duration,
                ),
            )
            for entity_result in result.meta.entity_results
            if self._policy.should_record(meta.operation_type, entity_result.status)
        ]
        await self._repository.atomic_create_fields(creations)
