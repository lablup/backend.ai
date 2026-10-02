from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

from callosum.rpc import RPCMessage
from callosum.rpc.message import RPCMessageTypes
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanContext, SpanKind

from ai.backend.agent.rpc.context import with_rpc_trace
from ai.backend.agent.rpc.middlewares.tracing import build_tracing_middleware
from ai.backend.agent.rpc.types import RPCMiddlewareContext
from ai.backend.agent.server import AgentRPCServer, RPCFunctionRegistry
from ai.backend.common.clients.agent.peer import PeerInvoker
from ai.backend.common.message_queue.types import MessageMetadata


def _request(method: str, body: dict[str, Any]) -> RPCMessage:
    return RPCMessage(None, RPCMessageTypes.FUNCTION, method, "", 0, None, body)


async def _traced_request(method: str) -> tuple[RPCMessage, SpanContext]:
    """The request ``PeerInvoker`` sends from inside a caller span, and that span."""
    peer = MagicMock()
    peer.invoke = AsyncMock()
    call = PeerInvoker._CallStub(peer)
    with trace.get_tracer(__name__).start_as_current_span("manager") as caller_span:
        await getattr(call, method)("k-1")
    _, request_body = peer.invoke.call_args.args
    return _request(method, request_body), caller_span.get_span_context()


def _rpc_span(exporter: InMemorySpanExporter, method: str) -> ReadableSpan:
    (span,) = [s for s in exporter.get_finished_spans() if s.name == method]
    return span


class TestRPCTraceContext:
    async def test_registry_handler_span_is_child_of_caller_span(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        registry = RPCFunctionRegistry()
        handler_trace_ids: list[int] = []

        async def destroy_kernel(self: AgentRPCServer, kernel_id: str) -> None:
            handler_trace_ids.append(trace.get_current_span().get_span_context().trace_id)

        request, caller = await _traced_request("destroy_kernel")
        await registry(destroy_kernel)(cast(AgentRPCServer, MagicMock()), request)

        agent_span = _rpc_span(span_exporter, "destroy_kernel")
        assert handler_trace_ids == [caller.trace_id]
        assert agent_span.kind == SpanKind.SERVER
        assert agent_span.parent is not None
        assert agent_span.parent.span_id == caller.span_id

    async def test_v3_middleware_span_is_child_of_caller_span(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        handler_trace_ids: list[int] = []

        async def handler(request: RPCMessage) -> None:
            handler_trace_ids.append(trace.get_current_span().get_span_context().trace_id)

        middleware = build_tracing_middleware()(RPCMiddlewareContext(method_name="get_logs"))
        request, caller = await _traced_request("get_logs")
        await middleware(handler)(request)

        agent_span = _rpc_span(span_exporter, "get_logs")
        assert handler_trace_ids == [caller.trace_id]
        assert agent_span.parent is not None
        assert agent_span.parent.span_id == caller.span_id

    def test_request_without_traceparent_opens_no_span(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        body = {"args": (), "kwargs": {}, "metadata": MessageMetadata().model_dump(mode="json")}

        with with_rpc_trace(_request("ping", body), "ping"):
            assert trace.get_current_span().get_span_context().is_valid is False

        assert span_exporter.get_finished_spans() == ()
