from __future__ import annotations

from typing import override

from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.actions.v2.lookup.bulk_monitor.base import BulkLookupActionMonitor
from ai.backend.manager.actions.v2.lookup.bulk_result import BulkLookupActionProcessResult
from ai.backend.manager.actions.v2.lookup.bulk_trigger import BulkLookupActionTriggerMeta
from ai.backend.manager.actions.v2.tracing import ActionTracer

__all__ = ("BulkLookupActionTracingMonitor",)


class BulkLookupActionTracingMonitor(BulkLookupActionMonitor):
    """Records each run as an OpenTelemetry span; registered first so the others run inside it.

    The span takes the first failed key's status, so a partly failed run is an error.
    A run with no results gets no status.
    """

    _tracer: ActionTracer

    def __init__(self) -> None:
        self._tracer = ActionTracer()

    @override
    async def prepare(self, meta: BulkLookupActionTriggerMeta) -> None:
        self._tracer.start_span(meta.action_name, meta.operation_type)

    @override
    async def done(
        self, meta: BulkLookupActionTriggerMeta, result: BulkLookupActionProcessResult
    ) -> None:
        if not result.meta.key_results:
            self._tracer.end_span(None, None, "")
            return
        for key_result in result.meta.key_results:
            if key_result.status is not OperationStatus.SUCCESS:
                self._tracer.end_span(
                    key_result.status, key_result.error_code, key_result.description
                )
                return
        self._tracer.end_span(OperationStatus.SUCCESS, None, "")
