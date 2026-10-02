from __future__ import annotations

from typing import Any, cast

from callosum.rpc import Peer
from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ai.backend.common.clients.agent.peer import PeerInvoker


class _RecordingPeer:
    bodies: list[dict[str, Any]]
    last_used: float

    def __init__(self) -> None:
        self.bodies = []
        self.last_used = 0.0

    async def invoke(self, name: str, body: dict[str, Any], order_key: str | None = None) -> None:
        self.bodies.append(body)


async def test_call_carries_the_caller_span_as_traceparent(
    span_exporter: InMemorySpanExporter,
) -> None:
    peer = _RecordingPeer()
    stub = PeerInvoker._CallStub(cast(Peer, peer))

    with trace.get_tracer(__name__).start_as_current_span("manager") as span:
        await stub.ping("ping")

    context = span.get_span_context()
    assert peer.bodies[0]["args"] == ("ping",)
    assert peer.bodies[0]["metadata"]["traceparent"] == (
        f"00-{context.trace_id:032x}-{context.span_id:016x}-01"
    )


async def test_call_without_context_carries_empty_metadata() -> None:
    peer = _RecordingPeer()
    stub = PeerInvoker._CallStub(cast(Peer, peer))

    await stub.ping("ping")

    assert peer.bodies[0]["metadata"] == {
        "request_id": None,
        "user": None,
        "triggered_user": None,
        "traceparent": None,
    }
