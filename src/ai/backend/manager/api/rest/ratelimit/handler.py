"""Rate-limit middleware handler.

This module provides the ``rlim_middleware`` function which is installed
as a global aiohttp middleware.  There are no route handlers — rate
limiting is applied transparently to all authorized requests.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.types import WebRequestHandler

if TYPE_CHECKING:
    from aiohttp.typedefs import Middleware
from ai.backend.manager.errors.api import RateLimitExceeded

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_RATELIMIT_WINDOW: Final = 60 * 15
_RATELIMIT_HEADERS_KEY: Final = "ratelimit_headers"


def _rlim_headers(rate_limit: int | None, remaining: int) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(rate_limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Window": str(_RATELIMIT_WINDOW),
    }


def make_rlim_middleware(
    valkey_client: ValkeyRateLimitClient,
) -> Middleware:
    """Create a rate-limit middleware that captures *valkey_client* via closure."""

    @web.middleware
    async def rlim_middleware(
        request: web.Request,
        handler: WebRequestHandler,
    ) -> web.StreamResponse:
        """Global middleware implementing a rolling-counter rate limiter."""
        if request["is_authorized"]:
            rate_limit = request["keypair"]["rate_limit"]
            rolling_count = await valkey_client.execute_rate_limit_logic(
                user_id=request["user"]["uuid"],
                window=_RATELIMIT_WINDOW,
            )
            if rate_limit is not None and rolling_count > rate_limit:
                request[_RATELIMIT_HEADERS_KEY] = _rlim_headers(rate_limit, 0)
                raise RateLimitExceeded
            remaining = rate_limit - rolling_count if rate_limit is not None else rolling_count
            request[_RATELIMIT_HEADERS_KEY] = _rlim_headers(rate_limit, remaining)
            return await handler(request)
        # No checks for rate limiting for non-authorized queries.
        request[_RATELIMIT_HEADERS_KEY] = _rlim_headers(1000, 1000)
        return await handler(request)

    return rlim_middleware


async def apply_rlim_headers(request: web.Request, response: web.StreamResponse) -> None:
    """``on_response_prepare`` hook: copy the headers set by ``rlim_middleware`` onto any response."""
    headers = request.get(_RATELIMIT_HEADERS_KEY)
    if headers is not None:
        response.headers.update(headers)
