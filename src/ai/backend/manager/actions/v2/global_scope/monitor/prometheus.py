from __future__ import annotations

from typing import override

from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor.base import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.result import GlobalActionProcessResult

__all__ = ("GlobalActionPrometheusMonitor",)


class GlobalActionPrometheusMonitor(GlobalActionMonitor):
    """Observes global action outcomes into the Prometheus action metrics."""

    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseGlobalAction, result: GlobalActionProcessResult) -> None:
        self._observer.observe_action(
            entity_type=action.entity_type(),
            operation_type=action.operation_type(),
            status=result.meta.status,
            duration=result.meta.duration.total_seconds(),
            error_code=result.meta.error_code,
        )
