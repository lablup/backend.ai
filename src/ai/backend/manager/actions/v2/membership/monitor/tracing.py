from __future__ import annotations

from typing import override

from ai.backend.manager.actions.v2.membership.monitor.base import MembershipActionMonitor
from ai.backend.manager.actions.v2.membership.result import MembershipActionProcessResult
from ai.backend.manager.actions.v2.membership.trigger import MembershipActionTriggerMeta
from ai.backend.manager.actions.v2.tracing import ActionTracer

__all__ = ("MembershipActionTracingMonitor",)


class MembershipActionTracingMonitor(MembershipActionMonitor):
    """Records each run as an OpenTelemetry span; registered first so the others run inside it."""

    _tracer: ActionTracer

    def __init__(self) -> None:
        self._tracer = ActionTracer()

    @override
    async def prepare(self, meta: MembershipActionTriggerMeta) -> None:
        self._tracer.start_span(meta.action_name, meta.operation_type)

    @override
    async def done(
        self, meta: MembershipActionTriggerMeta, result: MembershipActionProcessResult
    ) -> None:
        self._tracer.end_span(result.meta.status, result.meta.error_code, result.meta.description)
