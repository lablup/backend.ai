from __future__ import annotations

from typing import override

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import BulkActionProcessResult
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.tracing import ActionTracer

__all__ = ("BulkActionTracingMonitor",)


class BulkActionTracingMonitor(BulkActionMonitor):
    """Records each run as an OpenTelemetry span; registered first so the others run inside it.

    The span takes the first failed entity's status, so a partly failed run is an error.
    A run with no results gets no status.
    """

    _tracer: ActionTracer

    def __init__(self) -> None:
        self._tracer = ActionTracer()

    @override
    async def prepare(self, meta: BulkActionTriggerMeta) -> None:
        self._tracer.start_span(meta.action_name, meta.operation_type)

    @override
    async def done(self, meta: BulkActionTriggerMeta, result: BulkActionProcessResult) -> None:
        if not result.meta.entity_results:
            self._tracer.end_span(None, None, "")
            return
        for entity_result in result.meta.entity_results:
            if entity_result.status is not OperationStatus.SUCCESS:
                self._tracer.end_span(
                    entity_result.status, entity_result.error_code, entity_result.description
                )
                return
        self._tracer.end_span(OperationStatus.SUCCESS, None, "")
