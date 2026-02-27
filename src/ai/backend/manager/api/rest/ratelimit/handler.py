"""Rate-limit middleware handler.

This module provides the ``rlim_middleware`` function which is installed
as a global aiohttp middleware.  There are no route handlers — rate
limiting is applied transparently to all authorized requests.
"""

from __future__ import annotations

import logging
from typing import Final

from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.types import WebRequestHandler
from ai.backend.manager.errors.api import RateLimitExceeded

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_rlim_window: Final = 60 * 15


@web.middleware
async def rlim_middleware(
    app: web.Application,
    request: web.Request,
    handler: WebRequestHandler,
) -> web.StreamResponse:
    """Global middleware implementing a rolling-counter rate limiter."""
    app_ctx = app["ratelimit.context"]
    valkey_client: ValkeyRateLimitClient = app_ctx.valkey_rate_limit_client
    if request["is_authorized"]:
        rate_limit = request["keypair"]["rate_limit"]
        access_key = request["keypair"]["access_key"]
        rolling_count = await valkey_client.execute_rate_limit_logic(
            access_key=access_key,
            window=_rlim_window,
        )
        if rate_limit is not None and rolling_count > rate_limit:
            raise RateLimitExceeded
        remaining = rate_limit - rolling_count if rate_limit is not None else rolling_count
        response = await handler(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(_rlim_window)
        return response
    # No checks for rate limiting for non-authorized queries.
    response = await handler(request)
    response.headers["X-RateLimit-Limit"] = "1000"
    response.headers["X-RateLimit-Remaining"] = "1000"
    response.headers["X-RateLimit-Window"] = str(_rlim_window)
    return response
