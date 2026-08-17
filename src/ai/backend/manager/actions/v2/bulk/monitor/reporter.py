from __future__ import annotations

from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import BulkActionProcessResult
from ai.backend.manager.reporters.base import FinishedActionMessage, StartedActionMessage
from ai.backend.manager.reporters.hub import ReporterHub

__all__ = ("BulkActionReporterMonitor",)


class BulkActionReporterMonitor(BulkActionMonitor):
    """Reports the start and end of a bulk action run to the reporter hub.

    A reporter message carries a single ``entity_id``, so a bulk run fans out into
    one message per target entity; the messages share the ``action_id``, which ties
    them back to the same run.
    """

    _reporter_hub: ReporterHub

    def __init__(self, reporter_hub: ReporterHub) -> None:
        self._reporter_hub = reporter_hub

    @override
    async def prepare(self, meta: BulkActionTriggerMeta) -> None:
        # triggered_by = the caller who triggered the request; acted_as = the effective
        # (acting) subject. They differ only while a super admin is impersonating.
        trigger = triggered_user()
        acting = current_user()
        request_id = current_request_id()
        for entity_id in meta.entity_ids:
            message = StartedActionMessage(
                action_id=meta.action_id,
                action_type=meta.action_name,
                entity_id=entity_id,
                entity_type=meta.entity_type,
                request_id=request_id,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                operation_type=meta.operation_type,
                created_at=meta.started_at,
            )
            await self._reporter_hub.report_started(message)

    @override
    async def done(self, meta: BulkActionTriggerMeta, result: BulkActionProcessResult) -> None:
        trigger = triggered_user()
        acting = current_user()
        request_id = current_request_id() or BLANK_ID
        for entity_result in result.meta.entity_results:
            message = FinishedActionMessage(
                action_id=result.meta.action_id,
                action_type=meta.action_name,
                entity_id=entity_result.entity_id,
                request_id=request_id,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                entity_type=meta.entity_type,
                operation_type=meta.operation_type,
                status=entity_result.status,
                description=entity_result.description,
                created_at=result.meta.started_at,
                ended_at=result.meta.ended_at,
                duration=result.meta.duration,
            )
            await self._reporter_hub.report_finished(message)
