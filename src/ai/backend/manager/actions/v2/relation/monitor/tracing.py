from __future__ import annotations

from typing import override

from ai.backend.manager.actions.v2.relation.monitor.base import RelationActionMonitor
from ai.backend.manager.actions.v2.relation.result import RelationActionProcessResult
from ai.backend.manager.actions.v2.relation.trigger import RelationActionTriggerMeta
from ai.backend.manager.actions.v2.tracing import ActionTracer

__all__ = ("RelationActionTracingMonitor",)


class RelationActionTracingMonitor(RelationActionMonitor):
    """Records each run as an OpenTelemetry span; registered first so the others run inside it."""

    _tracer: ActionTracer

    def __init__(self) -> None:
        self._tracer = ActionTracer()

    @override
    async def prepare(self, meta: RelationActionTriggerMeta) -> None:
        self._tracer.start_span(meta.action_name, meta.operation_type)

    @override
    async def done(
        self, meta: RelationActionTriggerMeta, result: RelationActionProcessResult
    ) -> None:
        self._tracer.end_span(result.meta.status, result.meta.error_code, result.meta.description)
