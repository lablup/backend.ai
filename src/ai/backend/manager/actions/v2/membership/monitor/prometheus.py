from __future__ import annotations

from typing import override

from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.v2.membership.monitor.base import MembershipActionMonitor
from ai.backend.manager.actions.v2.membership.result import MembershipActionProcessResult
from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta

__all__ = ("MembershipActionPrometheusMonitor",)


class MembershipActionPrometheusMonitor(MembershipActionMonitor):
    """Observes membership move results into the Prometheus action metrics."""

    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, meta: MembershipActionTriggerMeta) -> None:
        return

    @override
    async def done(
        self, meta: MembershipActionTriggerMeta, result: MembershipActionProcessResult
    ) -> None:
        self._observer.observe_action(
            operation_type=meta.operation_type,
            status=result.meta.status,
            duration=result.meta.duration.total_seconds(),
        )
