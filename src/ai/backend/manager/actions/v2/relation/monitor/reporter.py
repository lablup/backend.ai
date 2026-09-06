from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.relation.monitor.base import RelationActionMonitor
from ai.backend.manager.actions.v2.relation.result import RelationActionProcessResult
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta
from ai.backend.manager.reporters.base import FinishedActionMessage, StartedActionMessage
from ai.backend.manager.reporters.hub import ReporterHub

__all__ = ("RelationActionReporterMonitor",)


class RelationActionReporterMonitor(RelationActionMonitor):
    """Reports the start and end of a link or unlink to the reporter hub.

    A message carries one entity, so a run fans out into one message per named scope —
    every scope is an entity, so each is reported as the one it is. The messages share
    the ``action_id``.
    """

    _reporter_hub: ReporterHub

    def __init__(self, reporter_hub: ReporterHub) -> None:
        self._reporter_hub = reporter_hub

    @override
    async def prepare(self, meta: RelationActionTriggerMeta) -> None:
        # triggered_by = the caller who triggered the request; acted_as = the effective
        # (acting) subject. They differ only while a super admin is impersonating.
        trigger = triggered_user()
        acting = current_user()
        request_id = current_request_id()
        for scope in meta.scope_targets:
            await self._reporter_hub.report_started(
                StartedActionMessage(
                    action_id=meta.action_id,
                    action_type=meta.action_name,
                    entity_id=scope.scope_id,
                    entity_type=EntityType(scope.scope_type),
                    request_id=request_id,
                    triggered_by=str(trigger.user_id) if trigger else None,
                    acted_as=acting.user_id if acting else None,
                    operation_type=meta.operation_type,
                    created_at=meta.started_at,
                )
            )

    @override
    async def done(
        self, meta: RelationActionTriggerMeta, result: RelationActionProcessResult
    ) -> None:
        trigger = triggered_user()
        acting = current_user()
        request_id = current_request_id() or BLANK_ID
        for scope in meta.scope_targets:
            await self._reporter_hub.report_finished(
                FinishedActionMessage(
                    action_id=meta.action_id,
                    action_type=meta.action_name,
                    entity_id=scope.scope_id,
                    request_id=request_id,
                    triggered_by=str(trigger.user_id) if trigger else None,
                    acted_as=acting.user_id if acting else None,
                    entity_type=EntityType(scope.scope_type),
                    operation_type=meta.operation_type,
                    status=result.meta.status,
                    description=result.meta.description,
                    created_at=meta.started_at,
                    ended_at=result.meta.ended_at,
                    duration=result.meta.duration,
                )
            )
