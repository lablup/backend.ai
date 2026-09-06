from __future__ import annotations

from typing import override

from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.v2.relation.monitor.base import RelationActionMonitor
from ai.backend.manager.actions.v2.relation.result import RelationActionProcessResult
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta

__all__ = ("RelationActionPrometheusMonitor",)


class RelationActionPrometheusMonitor(RelationActionMonitor):
    """Observes link and unlink outcomes into the Prometheus action metrics.

    One observation per run and none per entity: the run writes one row, and the metric
    names entities by kind, which a relation has none of.
    """

    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, meta: RelationActionTriggerMeta) -> None:
        return

    @override
    async def done(
        self, meta: RelationActionTriggerMeta, result: RelationActionProcessResult
    ) -> None:
        self._observer.observe_action(
            operation_type=meta.operation_type,
            status=result.meta.status,
            duration=result.meta.duration.total_seconds(),
        )
