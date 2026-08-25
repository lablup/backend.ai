from __future__ import annotations

from typing import override

from ai.backend.common.contexts.client_ip import current_client_ip
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction, LookupKey
from ai.backend.manager.actions.v2.lookup.monitor.base import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.result import LookupActionProcessResult
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingTarget
from ai.backend.manager.models.audit_log.creators import (
    LookupAuditLogCreator,
    MissedLookupAuditLogCreator,
)
from ai.backend.manager.repositories.client_ip_masking.repository import (
    ClientIPMaskingRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

__all__ = ("LookupActionAuditLogMonitor",)


class LookupActionAuditLogMonitor(LookupActionMonitor):
    """Persists an audit-log row for a lookup.

    The key is what identifies the row; ``entity_id`` carries what the key resolved to
    and stays NULL when the run did not get that far — a denial on the resolved entity
    still names it. Putting the key in ``entity_id`` is the conflation these columns
    exist to undo.

    Successful lookups are not recorded by default, but that is not a special case: a
    lookup reads, so the ordinary rule for reads applies to it unchanged.
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
    async def prepare(self, action: BaseLookupAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseLookupAction, result: LookupActionProcessResult) -> None:
        meta = result.meta
        if not self._policy.should_record(action.operation_type(), meta.status):
            return
        key = action.lookup_key()
        trigger = triggered_user()
        acting = current_user()
        client_ip = await self._client_ip_masking.mask(
            ClientIPMaskingTarget.AUDIT_LOGS, current_client_ip()
        )
        if meta.entity_id is None:
            # The key named nothing, so only the key itself identifies the row.
            await self._repository.create_dangling_field(
                action.entity_type(),
                MissedLookupAuditLogCreator(
                    action_id=meta.action_id,
                    operation=action.operation_type(),
                    action_name=action.action_name(),
                    created_at=meta.started_at,
                    description=meta.description,
                    status=meta.status,
                    lookup_kind=key.kind(),
                    lookup_key=self._render_key(key),
                    request_id=current_request_id() or BLANK_ID,
                    triggered_by=str(trigger.user_id) if trigger else None,
                    acted_as=acting.user_id if acting else None,
                    duration=meta.duration,
                    client_ip=client_ip,
                ),
            )
            return
        await self._repository.create_field(
            meta.entity_id,
            LookupAuditLogCreator(
                action_id=meta.action_id,
                operation=action.operation_type(),
                action_name=action.action_name(),
                created_at=meta.started_at,
                description=meta.description,
                status=meta.status,
                lookup_kind=key.kind(),
                lookup_key=self._render_key(key),
                request_id=current_request_id() or BLANK_ID,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                duration=meta.duration,
                client_ip=client_ip,
            ),
        )

    def _render_key(self, key: LookupKey) -> str:
        """Render the key as one filterable string.

        Components are emitted in sorted order, so a stored key is stable and a prefix
        match on the leading one works: ``domain_name=default,`` finds every lookup in
        that domain.
        """
        return ",".join(f"{name}={value}" for name, value in sorted(key.to_dict().items()))
