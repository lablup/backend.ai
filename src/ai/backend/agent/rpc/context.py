from __future__ import annotations

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager

from callosum.rpc import RPCMessage

from ai.backend.common.message_queue.types import MessageMetadata
from ai.backend.common.types import AgentId
from ai.backend.logging.structured import LogValue, with_log_context


@contextmanager
def with_rpc_context(request: RPCMessage, agent_id: AgentId, **fields: LogValue) -> Iterator[None]:
    """Restore the caller's metadata when the request carries it and scope logs to the RPC."""
    with ExitStack() as stack:
        raw_metadata = request.body.get("metadata") if request.body else None
        if raw_metadata is not None:
            metadata = MessageMetadata.model_validate(raw_metadata)
            stack.enter_context(metadata.apply_context())
        stack.enter_context(
            with_log_context(rpc_method=request.method, agent_id=agent_id, **fields)
        )
        yield
