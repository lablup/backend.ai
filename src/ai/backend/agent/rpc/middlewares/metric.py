"""RPC metric middleware for agent RPC v3.

Factory for a ``RPCMiddlewareProvider`` that records per-method request
latency and success/failure counters via ``RPCMetricObserver``. The
metric shape matches ``AgentRPCServer._collect_metrics`` for v1/v2, so
v3 dispatches land on the same histograms / counters under existing
dashboards.

Designed to be passed in via ``AgentRPCRegistry(..., middlewares=[...])``
so metric collection is a deliberate injected concern rather than a
registry-internal hard-coding.
"""

from __future__ import annotations

import functools
import time
from typing import Any

from callosum.rpc import RPCMessage

from ai.backend.agent.metrics.metric import RPCMetricObserver
from ai.backend.agent.rpc.types import (
    CallosumHandler,
    RPCMiddleware,
    RPCMiddlewareContext,
    RPCMiddlewareProvider,
)


def build_metric_middleware(
    observer: RPCMetricObserver,
) -> RPCMiddlewareProvider:
    """Construct a middleware provider that records RPC metrics."""

    def provider(ctx: RPCMiddlewareContext) -> RPCMiddleware:
        method_name = ctx.method_name

        def middleware(handler: CallosumHandler) -> CallosumHandler:
            @functools.wraps(handler)
            async def wrapped(request: RPCMessage) -> Any:
                start_time = time.perf_counter()
                try:
                    result = await handler(request)
                except BaseException as e:
                    observer.observe_rpc_request_failure(
                        method=method_name,
                        duration=time.perf_counter() - start_time,
                        exception=e,
                    )
                    raise
                else:
                    observer.observe_rpc_request_success(
                        method=method_name,
                        duration=time.perf_counter() - start_time,
                    )
                    return result

            return wrapped

        return middleware

    return provider
