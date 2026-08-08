from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction, LookupKey
from ai.backend.manager.actions.v2.lookup.monitor.base import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.result import LookupActionProcessResult
from ai.backend.manager.repositories.audit_log.creators import LookupAuditLogCreatorSpec
from ai.backend.manager.repositories.audit_log.repository import AuditLogRepository
from ai.backend.manager.repositories.base import Creator

__all__ = ("LookupActionAuditLogMonitor",)


class LookupActionAuditLogMonitor(LookupActionMonitor):
    """Persists an audit-log row for a lookup that did not resolve.

    A lookup has no entity id — producing one is what the run failed to do — so the
    key it was looking for is what identifies the row, and ``entity_id`` stays NULL.
    Putting the name in ``entity_id`` is the conflation these columns exist to undo.

    Successful lookups are not recorded by default, but that is not a special case: a
    lookup reads, so the ordinary rule for reads applies to it unchanged.
    """

    _repository: AuditLogRepository
    _policy: AuditLogPolicy

    def __init__(self, repository: AuditLogRepository, policy: AuditLogPolicy) -> None:
        self._repository = repository
        self._policy = policy

    @override
    async def prepare(self, action: BaseLookupAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseLookupAction, result: LookupActionProcessResult) -> None:
        meta = result.meta
        if not self._policy.should_record(action.spec(), meta.status):
            return
        key = action.lookup_key()
        trigger = triggered_user()
        acting = current_user()
        creator = Creator(
            spec=LookupAuditLogCreatorSpec(
                action_id=meta.action_id,
                entity_type=action.entity_type(),
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
            )
        )
        await self._repository.create(creator)

    def _render_key(self, key: LookupKey) -> str:
        """Render the key as one filterable string.

        Components are emitted in sorted order, so a stored key is stable and a prefix
        match on the leading one works: ``domain_name=default,`` finds every lookup in
        that domain.
        """
        return ",".join(f"{name}={value}" for name, value in sorted(key.to_dict().items()))
