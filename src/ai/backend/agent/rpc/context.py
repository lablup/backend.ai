from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager

from callosum.rpc import RPCMessage
from opentelemetry.trace import SpanKind

from ai.backend.common.message_queue.types import MessageMetadata


@contextmanager
def with_rpc_trace(request: RPCMessage, span_name: str) -> Iterator[None]:
    """Open the RPC span under the caller's span when the request carries one."""
    raw_metadata = request.body.get("metadata") if request.body else None
    traceparent = raw_metadata.get("traceparent") if isinstance(raw_metadata, Mapping) else None
    metadata = MessageMetadata(traceparent=traceparent if isinstance(traceparent, str) else None)
    with metadata.continue_trace(span_name, SpanKind.SERVER):
        yield
