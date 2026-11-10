from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.membership.monitor.base import MembershipActionMonitor
from ai.backend.manager.actions.v2.membership.result import MembershipActionProcessResult
from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta
from ai.backend.manager.reporters.base import FinishedActionMessage, StartedActionMessage
from ai.backend.manager.reporters.hub import ReporterHub

__all__ = ("MembershipActionReporterMonitor",)


class MembershipActionReporterMonitor(MembershipActionMonitor):
    """Reports the start and end of a membership move, as the moved entity."""

    _reporter_hub: ReporterHub

    def __init__(self, reporter_hub: ReporterHub) -> None:
        self._reporter_hub = reporter_hub

    @override
    async def prepare(self, meta: MembershipActionTriggerMeta) -> None:
        trigger = triggered_user()
        acting = current_user()
        await self._reporter_hub.report_started(
            StartedActionMessage(
                action_id=meta.action_id,
                action_type=meta.action_name,
                entity_id=meta.entity,
                entity_type=meta.entity.entity_type(),
                request_id=current_request_id(),
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                operation_type=meta.operation_type,
                created_at=meta.started_at,
            )
        )

    @override
    async def done(
        self, meta: MembershipActionTriggerMeta, result: MembershipActionProcessResult
    ) -> None:
        trigger = triggered_user()
        acting = current_user()
        await self._reporter_hub.report_finished(
            FinishedActionMessage(
                action_id=meta.action_id,
                action_type=meta.action_name,
                entity_id=meta.entity,
                request_id=current_request_id() or BLANK_ID,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                entity_type=meta.entity.entity_type(),
                operation_type=meta.operation_type,
                status=result.meta.status,
                description=result.meta.description,
                created_at=meta.started_at,
                ended_at=result.meta.ended_at,
                duration=result.meta.duration,
            )
        )
