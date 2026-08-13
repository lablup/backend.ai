from __future__ import annotations

from typing import override

from ai.backend.common.metrics.metric import ActionMetricObserver
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.lookup.monitor.base import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.result import LookupActionProcessResult

__all__ = ("LookupActionPrometheusMonitor",)


class LookupActionPrometheusMonitor(LookupActionMonitor):
    """Counts lookups by the shape of the key, which is the legacy-drain indicator.

    A lookup exists to bridge an external key to an internal id while callers still
    use the key. When a shape's counter stops moving, that lookup can be removed.
    """

    _observer: ActionMetricObserver

    def __init__(self) -> None:
        self._observer = ActionMetricObserver.instance()

    @override
    async def prepare(self, action: BaseLookupAction, meta: BaseActionTriggerMeta) -> None:
        return

    @override
    async def done(self, action: BaseLookupAction, result: LookupActionProcessResult) -> None:
        self._observer.observe_lookup(
            entity_type=action.entity_type(),
            lookup_kind=action.lookup_key().kind(),
            status=result.meta.status,
        )
