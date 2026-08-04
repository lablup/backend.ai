from __future__ import annotations

from typing import override

from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.result import ScopeActionProcessResult

__all__ = ("ScopeActionPrometheusMonitor",)


class ScopeActionPrometheusMonitor(ScopeActionMonitor):
    """Observes scope action results into the Prometheus action metrics.

    The run is observed once, so ``backendai_action_count`` stays a count of requests.
    The entities it affected are counted separately — a scope run can touch any number
    of them, which the per-run metric cannot show. They share the run's status: a scope
    action reports which entities it affected, not a status for each.
    """

    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseScopeAction, result: ScopeActionProcessResult) -> None:
        meta = result.meta
        self._observer.observe_action(
            entity_type=action.entity_type(),
            operation_type=action.operation_type(),
            status=meta.status,
            duration=meta.duration.total_seconds(),
            error_code=meta.error_code,
        )
        for _ in meta.entity_ids:
            self._observer.observe_action_entity(
                entity_type=action.entity_type(),
                operation_type=action.operation_type(),
                status=meta.status,
                error_code=meta.error_code,
            )
