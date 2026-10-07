"""RPC tracing middleware for agent RPC v3.

Opens the RPC span under the caller's span carried in the request metadata.
Register it first so the other middlewares run inside the span.
"""

from __future__ import annotations

import functools
from typing import Any

from callosum.rpc import RPCMessage

from ai.backend.agent.rpc.context import with_rpc_trace
from ai.backend.agent.rpc.types import (
    CallosumHandler,
    RPCMiddleware,
    RPCMiddlewareContext,
    RPCMiddlewareProvider,
)


def build_tracing_middleware() -> RPCMiddlewareProvider:
    """Construct a middleware provider that opens an RPC span."""

    def provider(ctx: RPCMiddlewareContext) -> RPCMiddleware:
        method_name = ctx.method_name

        def middleware(handler: CallosumHandler) -> CallosumHandler:
            @functools.wraps(handler)
            async def wrapped(request: RPCMessage) -> Any:
                with with_rpc_trace(request, method_name):
                    return await handler(request)

            return wrapped

        return middleware

    return provider
