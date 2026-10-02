from __future__ import annotations

from typing import override

from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor.base import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.result import GlobalActionProcessResult
from ai.backend.manager.actions.v2.tracing import ActionTracer
from ai.backend.manager.actions.v2.trigger import ActionTriggerMeta

__all__ = ("GlobalActionTracingMonitor",)


class GlobalActionTracingMonitor(GlobalActionMonitor):
    """Records each run as an OpenTelemetry span; registered first so the others run inside it."""

    _tracer: ActionTracer

    def __init__(self) -> None:
        self._tracer = ActionTracer()

    @override
    async def prepare(self, action: BaseGlobalAction, meta: ActionTriggerMeta) -> None:
        self._tracer.start_span(action.action_name(), action.operation_type())

    @override
    async def done(self, action: BaseGlobalAction, result: GlobalActionProcessResult) -> None:
        self._tracer.end_span(result.meta.status, result.meta.error_code, result.meta.description)
