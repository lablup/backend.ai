from __future__ import annotations

from typing import override

from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.v2.single_entity.trigger import (
    SingleEntityActionTriggerMeta,
)

__all__ = ("SingleEntityActionPrometheusMonitor",)


class SingleEntityActionPrometheusMonitor(SingleEntityActionMonitor):
    """Observes single-entity action outcomes into the Prometheus action metrics."""

    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, meta: SingleEntityActionTriggerMeta) -> None:
        return

    @override
    async def done(
        self, meta: SingleEntityActionTriggerMeta, result: SingleEntityActionProcessResult
    ) -> None:
        self._observer.observe_action(
            entity_type=meta.entity.entity_type(),
            operation_type=meta.operation_type,
            status=result.meta.status,
            duration=result.meta.duration.total_seconds(),
            error_code=result.meta.error_code,
        )
