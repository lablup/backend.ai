from __future__ import annotations

from typing import override

from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.bulk.base import BaseBulkAction
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import BulkActionProcessResult

__all__ = ("BulkActionPrometheusMonitor",)


class BulkActionPrometheusMonitor(BulkActionMonitor):
    """Observes bulk action outcomes into the Prometheus action metrics.

    One observation per run — the action metric is keyed by (entity_type,
    operation, status), not by target, so a bulk run does not fan out.
    """

    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, action: BaseBulkAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseBulkAction, result: BulkActionProcessResult) -> None:
        self._observer.observe_action(
            entity_type=action.entity_type(),
            operation_type=action.operation_type(),
            status=result.meta.status,
            duration=result.meta.duration.total_seconds(),
            error_code=result.meta.error_code,
        )
