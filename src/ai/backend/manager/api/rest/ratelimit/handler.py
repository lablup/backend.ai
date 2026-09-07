"""Rate-limit middleware handler.

This module provides the ``rlim_middleware`` function which is installed
as a global aiohttp middleware.  There are no route handlers — rate
limiting is applied transparently to all authorized requests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from aiohttp import web
from multidict import CIMultiDict

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.web.reserved_response_headers import reserve_response_headers
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.types import WebRequestHandler

if TYPE_CHECKING:
    from aiohttp.typedefs import Middleware
from ai.backend.manager.errors.api import RateLimitExceeded

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_RATELIMIT_WINDOW_SECONDS: Final = 60 * 15
_ANONYMOUS_RATELIMIT: Final = 1000


@dataclass(frozen=True)
class RateLimitQuota:
    limit: int
    remaining: int
    reset_after_seconds: int
    window_seconds: int

    def apply_to(self, headers: CIMultiDict[str]) -> None:
        headers["X-RateLimit-Limit"] = str(self.limit)
        headers["X-RateLimit-Remaining"] = str(self.remaining)
        headers["X-RateLimit-Reset"] = str(self.reset_after_seconds)
        headers["X-RateLimit-Window"] = str(self.window_seconds)


def make_rlim_middleware(
    valkey_client: ValkeyRateLimitClient,
) -> Middleware:
    """Create a rate-limit middleware that captures *valkey_client* via closure."""

    @web.middleware
    async def rlim_middleware(
        request: web.Request,
        handler: WebRequestHandler,
    ) -> web.StreamResponse:
        """Global middleware implementing a fixed-window rate limiter."""
        if request["is_authorized"]:
            state = await valkey_client.consume_rate_limit(
                user_id=request["user"]["uuid"],
                window_seconds=_RATELIMIT_WINDOW_SECONDS,
                limit=request["user"]["rate_limit"],
            )
            if state.count > state.limit:
                reserve_response_headers(
                    request,
                    RateLimitQuota(
                        limit=state.limit,
                        remaining=0,
                        reset_after_seconds=state.reset_after_seconds,
                        window_seconds=_RATELIMIT_WINDOW_SECONDS,
                    ),
                )
                raise RateLimitExceeded
            reserve_response_headers(
                request,
                RateLimitQuota(
                    limit=state.limit,
                    remaining=state.limit - state.count,
                    reset_after_seconds=state.reset_after_seconds,
                    window_seconds=_RATELIMIT_WINDOW_SECONDS,
                ),
            )
            return await handler(request)
        # No checks for rate limiting for non-authorized queries.
        reserve_response_headers(
            request,
            RateLimitQuota(
                limit=_ANONYMOUS_RATELIMIT,
                remaining=_ANONYMOUS_RATELIMIT,
                reset_after_seconds=_RATELIMIT_WINDOW_SECONDS,
                window_seconds=_RATELIMIT_WINDOW_SECONDS,
            ),
        )
        return await handler(request)

    return rlim_middleware
