from __future__ import annotations

from typing import override

from ai.backend.common.contexts.client_ip import current_client_ip
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.relation.monitor.base import RelationActionMonitor
from ai.backend.manager.actions.v2.relation.result import RelationActionProcessResult
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingTarget
from ai.backend.manager.models.audit_log.creators import (
    AuditLogScopeCreator,
    RelationAuditLogCreator,
)
from ai.backend.manager.repositories.client_ip_masking.repository import (
    ClientIPMaskingRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = ("RelationActionAuditLogMonitor",)


class RelationActionAuditLogMonitor(RelationActionMonitor):
    """Persists one audit-log row per link or unlink.

    The row names no entity and no kind — what the run wrote stands between two entities
    and is neither of them. Which two it was about is on ``audit_log_scopes``, the same
    place a scope run's targets go.
    """

    _repository: OpsRepository[AuditLogData]
    _policy: AuditLogPolicy
    _client_ip_masking: ClientIPMaskingRepository

    def __init__(
        self,
        repository: OpsRepository[AuditLogData],
        policy: AuditLogPolicy,
        client_ip_masking: ClientIPMaskingRepository,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._client_ip_masking = client_ip_masking

    @override
    async def prepare(self, meta: RelationActionTriggerMeta) -> None:
        pass

    @override
    async def done(
        self, meta: RelationActionTriggerMeta, result: RelationActionProcessResult
    ) -> None:
        if not self._policy.should_record(meta.operation_type, result.meta.status):
            return
        trigger = triggered_user()
        acting = current_user()
        client_ip = await self._client_ip_masking.mask(
            ClientIPMaskingTarget.AUDIT_LOGS, current_client_ip()
        )
        creator = RelationAuditLogCreator(
            entity_type=None,
            action_id=meta.action_id,
            operation=meta.operation_type,
            action_name=meta.action_name,
            created_at=meta.started_at,
            description=result.meta.description,
            status=result.meta.status,
            request_id=current_request_id() or BLANK_ID,
            triggered_by=str(trigger.user_id) if trigger else None,
            acted_as=acting.user_id if acting else None,
            duration=result.meta.duration,
            client_ip=client_ip,
        )
        await self._repository.atomic_create_dangling_fields_with_nested(
            [creator],
            [
                AuditLogScopeCreator(scope_type=str(scope.scope_type), scope_id=scope.scope_id)
                for scope in meta.scope_targets
            ],
        )
