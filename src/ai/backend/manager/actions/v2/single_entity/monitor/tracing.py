from __future__ import annotations

from typing import override

from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta
from ai.backend.manager.actions.v2.tracing import ActionTracer

__all__ = ("SingleEntityActionTracingMonitor",)


class SingleEntityActionTracingMonitor(SingleEntityActionMonitor):
    """Records each run as an OpenTelemetry span; registered first so the others run inside it."""

    _tracer: ActionTracer

    def __init__(self) -> None:
        self._tracer = ActionTracer()

    @override
    async def prepare(self, meta: SingleEntityActionTriggerMeta) -> None:
        self._tracer.start_span(meta.action_name, meta.operation_type)

    @override
    async def done(
        self, meta: SingleEntityActionTriggerMeta, result: SingleEntityActionProcessResult
    ) -> None:
        self._tracer.end_span(result.meta.status, result.meta.error_code, result.meta.description)
