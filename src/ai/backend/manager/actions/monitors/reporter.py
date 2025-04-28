from typing import Final, override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.reporters.base import FinishedActionMessage, StartedActionMessage
from ai.backend.manager.reporters.hub import ReporterHub

_BLANK_ID: Final[str] = "(unknown)"


class ReporterMonitor(ActionMonitor):
    _reporter_hub: ReporterHub

    def __init__(self, reporter_hub: ReporterHub) -> None:
        self._reporter_hub = reporter_hub

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        message = StartedActionMessage(
            action_id=meta.action_id,
            action_type=action.type(),
            entity_id=action.entity_id(),
            entity_type=action.entity_type(),
            request_id=current_request_id(),
            operation_type=action.operation_type(),
            created_at=meta.started_at,
        )
        await self._reporter_hub.report_started(message)

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        entity_id = action.entity_id()
        if not entity_id:
            entity_id = result.result.entity_id() if result.result else _BLANK_ID

        message = FinishedActionMessage(
            action_id=result.meta.action_id,
            action_type=action.type(),
            entity_id=entity_id,
            request_id=current_request_id() or _BLANK_ID,
            entity_type=action.entity_type(),
            operation_type=action.operation_type(),
            status=result.meta.status,
            description=result.meta.description,
            created_at=result.meta.started_at,
            ended_at=result.meta.ended_at,
            duration=result.meta.duration,
        )
        await self._reporter_hub.report_finished(message)
