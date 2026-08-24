from __future__ import annotations

from typing import Any, override

from ai.backend.common.contexts.client_ip import current_client_ip
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.result import ScopeActionProcessResult
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingTarget
from ai.backend.manager.models.audit_log.creators import (
    AuditLogScopeCreator,
    EmptyScopeAuditLogCreator,
    ScopeAuditLogCreator,
)
from ai.backend.manager.models.specs.creator import FieldToCreate
from ai.backend.manager.repositories.client_ip_masking.repository import (
    ClientIPMaskingRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = ("ScopeActionAuditLogMonitor",)


class ScopeActionAuditLogMonitor(ScopeActionMonitor):
    """Persists one audit-log row per entity a scope action affected.

    Rows are keyed on the entity, not the scope, so a run over several scopes is not
    mistaken for several runs. The scopes the request covered are attached to every
    row via ``audit_log_scopes``. A run that affected nothing still leaves one row.
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
    async def prepare(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseScopeAction, result: ScopeActionProcessResult) -> None:
        meta = result.meta
        if not self._policy.should_record(action.operation_type(), meta.status):
            return
        nested = [
            AuditLogScopeCreator(scope_type=str(s.scope_type), scope_id=s.scope_id)
            for s in meta.scope_targets
        ]
        client_ip = await self._client_ip_masking.mask(
            ClientIPMaskingTarget.AUDIT_LOGS, current_client_ip()
        )
        if meta.entity_ids:
            await self._repository.atomic_create_fields_with_nested(
                [
                    FieldToCreate(
                        owner_id=entity_id,
                        creator=self._build_spec(action, result, client_ip),
                    )
                    for entity_id in meta.entity_ids
                ],
                nested,
            )
            return
        # Nothing was touched, but the run still has to leave a trace.
        await self._repository.atomic_create_dangling_fields_with_nested(
            action.entity_type(),
            [self._build_empty_spec(action, result, client_ip)],
            nested,
        )

    def _build_spec(
        self,
        action: BaseScopeAction,
        result: ScopeActionProcessResult,
        client_ip: str | None,
    ) -> ScopeAuditLogCreator:
        return ScopeAuditLogCreator(**self._fields(action, result, client_ip))

    def _build_empty_spec(
        self,
        action: BaseScopeAction,
        result: ScopeActionProcessResult,
        client_ip: str | None,
    ) -> EmptyScopeAuditLogCreator:
        return EmptyScopeAuditLogCreator(**self._fields(action, result, client_ip))

    def _fields(
        self,
        action: BaseScopeAction,
        result: ScopeActionProcessResult,
        client_ip: str | None,
    ) -> dict[str, Any]:
        trigger = triggered_user()
        acting = current_user()
        meta = result.meta
        return {
            "action_id": meta.action_id,
            "operation": action.operation_type(),
            "action_name": action.action_name(),
            "created_at": meta.started_at,
            "description": meta.description,
            "status": meta.status,
            "request_id": current_request_id() or BLANK_ID,
            "triggered_by": str(trigger.user_id) if trigger else None,
            "acted_as": acting.user_id if acting else None,
            "duration": meta.duration,
            "client_ip": client_ip,
        }
