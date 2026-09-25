from __future__ import annotations

from typing import override

from ai.backend.common.contexts.client_ip import current_client_ip
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.membership.monitor.base import MembershipActionMonitor
from ai.backend.manager.actions.v2.membership.result import MembershipActionProcessResult
from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingTarget
from ai.backend.manager.models.audit_log.creators import (
    AuditLogScopeCreator,
    MembershipAuditLogCreator,
)
from ai.backend.manager.models.specs.creator import FieldToCreate
from ai.backend.manager.repositories.client_ip_masking.repository import (
    ClientIPMaskingRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = ("MembershipActionAuditLogMonitor",)


class MembershipActionAuditLogMonitor(MembershipActionMonitor):
    """Persists one audit-log row per membership move, under the moved entity; the
    scopes it moved through go to ``audit_log_scopes``."""

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
    async def prepare(self, meta: MembershipActionTriggerMeta) -> None:
        pass

    @override
    async def done(
        self, meta: MembershipActionTriggerMeta, result: MembershipActionProcessResult
    ) -> None:
        if not self._policy.should_record(meta.operation_type, result.meta.status):
            return
        trigger = triggered_user()
        acting = current_user()
        client_ip = await self._client_ip_masking.mask(
            ClientIPMaskingTarget.AUDIT_LOGS, current_client_ip()
        )
        creator = MembershipAuditLogCreator(
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
        await self._repository.atomic_create_fields_with_nested(
            [FieldToCreate(owner_id=meta.entity, creator=creator)],
            [
                AuditLogScopeCreator(scope_type=str(scope.entity_type()), scope_id=scope)
                for scope in meta.scopes
            ],
        )
