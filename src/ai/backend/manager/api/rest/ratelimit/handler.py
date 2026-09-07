"""Rate-limit middleware handler.

This module provides the ``rlim_middleware`` function which is installed
as a global aiohttp middleware.  There are no route handlers — rate
limiting is applied transparently to every request.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from aiohttp import web
from multidict import CIMultiDict

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.contexts.client_ip import current_client_ip
from ai.backend.common.exception import UnreachableError
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
        state: RateLimitState
        if request["is_authorized"]:
            state = await valkey_client.consume_user_rate_limit(
                user_id=request["user"]["uuid"],
                window_seconds=_RATELIMIT_WINDOW_SECONDS,
                limit=request["user"]["rate_limit"],
            )
        else:
            client_ip = current_client_ip()
            if client_ip is None:
                raise UnreachableError("a request over a socket always has a peer address")
            state = await valkey_client.consume_ip_rate_limit(
                client_ip=client_ip,
                window_seconds=_RATELIMIT_WINDOW_SECONDS,
                limit=_ANONYMOUS_RATELIMIT,
            )
        reserve_response_headers(
            request,
            RateLimitQuota(
                limit=state.limit,
                remaining=max(state.limit - state.count, 0),
                reset_after_seconds=state.reset_after_seconds,
                window_seconds=_RATELIMIT_WINDOW_SECONDS,
            ),
        )
        if state.count > state.limit:
            raise RateLimitExceeded
        return await handler(request)

    return rlim_middleware
