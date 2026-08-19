from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.result import ScopeActionProcessResult
from ai.backend.manager.reporters.base import FinishedActionMessage, StartedActionMessage
from ai.backend.manager.reporters.hub import ReporterHub

__all__ = ("ScopeActionReporterMonitor",)


class ScopeActionReporterMonitor(ScopeActionMonitor):
    """Reports the start and end of a scope action run to the reporter hub.

    A reporter message carries a single ``entity_id``, so a scope run fans out into
    one message per target scope with the scope's id recorded as ``entity_id``
    (matching the audit-log rows); the messages share the ``action_id``, which ties
    them back to the same run.
    """

    _reporter_hub: ReporterHub

    def __init__(self, reporter_hub: ReporterHub) -> None:
        self._reporter_hub = reporter_hub

    @override
    async def prepare(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        # triggered_by = the caller who triggered the request; acted_as = the effective
        # (acting) subject. They differ only while a super admin is impersonating.
        trigger = triggered_user()
        acting = current_user()
        request_id = current_request_id()
        for scope in action.scope_targets():
            message = StartedActionMessage(
                action_id=meta.action_id,
                action_type=action.spec().type(),
                entity_id=scope.scope_id,
                entity_type=action.entity_type(),
                request_id=request_id,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                operation_type=action.operation_type(),
                created_at=meta.started_at,
            )
            await self._reporter_hub.report_started(message)

    @override
    async def done(self, action: BaseScopeAction, result: ScopeActionProcessResult) -> None:
        trigger = triggered_user()
        acting = current_user()
        meta = result.meta
        request_id = current_request_id() or BLANK_ID
        for scope in meta.scope_targets:
            message = FinishedActionMessage(
                action_id=meta.action_id,
                action_type=action.spec().type(),
                entity_id=scope.scope_id,
                request_id=request_id,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                entity_type=action.entity_type(),
                operation_type=action.operation_type(),
                status=meta.status,
                description=meta.description,
                created_at=meta.started_at,
                ended_at=meta.ended_at,
                duration=meta.duration,
            )
            await self._reporter_hub.report_finished(message)
