from contextvars import ContextVar, Token
from dataclasses import dataclass

from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace import Span, StatusCode

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus

__all__ = ("ActionTracer",)


@dataclass(frozen=True)
class _OpenActionSpan:
    span: Span
    context_token: Token[Context]
    enclosing: "_OpenActionSpan | None"


_open_action_span: ContextVar[_OpenActionSpan | None] = ContextVar("open_action_span", default=None)


class ActionTracer:
    """Opens an action span as the current span in ``prepare`` and ends it in ``done``.

    Monitors are shared by concurrent runs, so the open span lives in a ContextVar.
    """

    def start_span(self, action_name: str, operation_type: ActionOperationType) -> None:
        span = trace.get_tracer(__name__).start_span(
            action_name,
            attributes={
                "backendai.action.name": action_name,
                "backendai.action.operation": str(operation_type),
            },
        )
        context_token = otel_context.attach(trace.set_span_in_context(span))
        _open_action_span.set(
            _OpenActionSpan(
                span=span, context_token=context_token, enclosing=_open_action_span.get()
            )
        )

    def end_span(
        self, status: OperationStatus | None, error_code: ErrorCode | None, description: str
    ) -> None:
        """End the open span. ``status`` is None when the run reported nothing to judge it by."""
        open_span = _open_action_span.get()
        if open_span is None:
            return
        _open_action_span.set(open_span.enclosing)
        otel_context.detach(open_span.context_token)
        span = open_span.span
        if status is not None:
            span.set_attribute("backendai.action.status", str(status))
            if status is not OperationStatus.SUCCESS:
                span.set_status(StatusCode.ERROR, description)
        if error_code is not None:
            span.set_attribute("backendai.error_code", str(error_code))
        span.end()
