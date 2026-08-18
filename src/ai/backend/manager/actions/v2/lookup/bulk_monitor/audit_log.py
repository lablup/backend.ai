from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.lookup.bulk_monitor.base import BulkLookupActionMonitor
from ai.backend.manager.actions.v2.lookup.bulk_result import BulkLookupActionProcessResult
from ai.backend.manager.actions.v2.lookup.bulk_trigger import BulkLookupActionTriggerMeta
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.creators import LookupAuditLogCreator
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = ("BulkLookupActionAuditLogMonitor",)


class BulkLookupActionAuditLogMonitor(BulkLookupActionMonitor):
    """Persists one audit-log row per key of a bulk lookup run.

    A key that named nothing leaves a row exactly as a single lookup's miss does — the
    key identifies it and ``entity_id`` stays NULL. The rows share the ``action_id``,
    which ties them back to the same run.
    """

    _repository: OpsRepository[AuditLogData]
    _policy: AuditLogPolicy

    def __init__(self, repository: OpsRepository[AuditLogData], policy: AuditLogPolicy) -> None:
        self._repository = repository
        self._policy = policy

    @override
    async def prepare(self, meta: BulkLookupActionTriggerMeta) -> None:
        pass

    @override
    async def done(
        self, meta: BulkLookupActionTriggerMeta, result: BulkLookupActionProcessResult
    ) -> None:
        trigger = triggered_user()
        acting = current_user()
        request_id = current_request_id() or BLANK_ID
        specs = [
            LookupAuditLogCreator(
                action_id=result.meta.action_id,
                entity_type=meta.entity_type,
                operation=meta.operation_type,
                action_name=meta.action_name,
                created_at=result.meta.started_at,
                description=key_result.description,
                status=key_result.status,
                lookup_kind=key_result.key.kind(),
                lookup_key=self._render_key(key_result.key),
                entity_id=key_result.entity_id,
                request_id=request_id,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                duration=result.meta.duration,
            )
            for key_result in result.meta.key_results
            if self._policy.should_record(meta.operation_type, key_result.status)
        ]
        if not specs:
            return
        await self._repository.atomic_create_sidecars(specs)

    def _render_key(self, key: LookupKey) -> str:
        """Rendered as the single lookup's is, so both are filterable the same way."""
        return ",".join(f"{name}={value}" for name, value in sorted(key.to_dict().items()))
