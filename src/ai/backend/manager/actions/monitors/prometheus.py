from typing import override

from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from ai.backend.manager.actions.monitors.monitor import ActionMonitor


class PrometheusMonitor(ActionMonitor):
    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        self._observer.observe_action(
            entity_type=action.entity_type(),
            operation_type=action.operation_type(),
            status=result.meta.status,
            duration=result.meta.duration.total_seconds(),
            error_code=result.meta.error_code,
        )
