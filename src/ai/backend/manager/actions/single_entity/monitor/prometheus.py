from typing import cast, override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.single_entity.result import SingleEntityActionProcessResult

__all__ = ("SingleEntityPrometheusMonitor",)


class SingleEntityPrometheusMonitor(SingleEntityActionMonitor):
    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(
        self, action: BaseSingleEntityAction, result: SingleEntityActionProcessResult
    ) -> None:
        self._observer.observe_action(
            entity_type=cast(EntityType, action.entity_type()),
            operation_type=action.operation_type(),
            status=result.meta.status,
            duration=result.meta.duration.total_seconds(),
            error_code=result.meta.error_code,
        )
