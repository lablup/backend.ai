from typing import cast, override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.reporters.base import FinishedActionMessage, StartedActionMessage
from ai.backend.manager.reporters.hub import ReporterHub

__all__ = ("SingleEntityReporterMonitor",)


class SingleEntityReporterMonitor(SingleEntityActionMonitor):
    _reporter_hub: ReporterHub

    def __init__(self, reporter_hub: ReporterHub) -> None:
        self._reporter_hub = reporter_hub

    @override
    async def prepare(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        trigger = triggered_user()
        acting = current_user()
        message = StartedActionMessage(
            action_id=meta.action_id,
            action_type=action.action_type(),
            entity_id=action.entity_id(),
            entity_type=cast(EntityType, action.entity_type()),
            request_id=current_request_id(),
            triggered_by=str(trigger.user_id) if trigger else None,
            acted_as=acting.user_id if acting else None,
            operation_type=action.operation_type(),
            created_at=meta.started_at,
        )
        await self._reporter_hub.report_started(message)

    @override
    async def done(
        self, action: BaseSingleEntityAction, result: SingleEntityActionProcessResult
    ) -> None:
        trigger = triggered_user()
        acting = current_user()
        message = FinishedActionMessage(
            action_id=result.meta.action_id,
            action_type=action.action_type(),
            entity_id=result.meta.entity_id,
            entity_type=cast(EntityType, action.entity_type()),
            request_id=current_request_id(),
            triggered_by=str(trigger.user_id) if trigger else None,
            acted_as=acting.user_id if acting else None,
            operation_type=action.operation_type(),
            status=result.meta.status,
            description=result.meta.description,
            created_at=result.meta.started_at,
            ended_at=result.meta.ended_at,
            duration=result.meta.duration,
        )
        await self._reporter_hub.report_finished(message)
