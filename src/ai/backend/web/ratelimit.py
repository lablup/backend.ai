"""Rate limiting for requests proxied to the manager.

Reads the window the manager-side limiter keeps — by user for a signed-in caller, by
address otherwise — and refuses once the count has reached the limit. Only the manager
counts.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Final

from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import (
    RateLimitState,
    ValkeyRateLimitClient,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import UnreachableError
from ai.backend.common.web.session import get_session
from ai.backend.logging import BraceStyleAdapter
from ai.backend.web.auth import get_client_ip

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_RATELIMIT_WINDOW: Final = 60 * 15

type Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


async def _read_ratelimit_window(request: web.Request) -> RateLimitState | None:
    """The window the manager will count this request in.

    None when this server cannot name one: a session stored before the login handler
    kept the user id, or no open window.
    """
    valkey_client: ValkeyRateLimitClient = request.app["valkey_rate_limit"]
    session = await get_session(request)
    if not session.get("authenticated", False):
        client_ip = get_client_ip(request)
        if client_ip is None:
            raise UnreachableError("a request over a socket always has a peer address")
        return await valkey_client.get_ip_rate_limit(client_ip)
    token = session.get("token") or {}
    # Both login handlers store the user id, but sessions outlive an upgrade in Redis:
    # one written before they did carries no user id.
    raw_user_id = token.get("user_id")
    if raw_user_id is None:
        return None
    return await valkey_client.get_user_rate_limit(UserID(uuid.UUID(raw_user_id)))


def manager_proxy_rate_limited(handler: Handler) -> Handler:
    """Wrap a manager proxy handler so the web server rejects over-limit requests."""

    async def rlim_handler(request: web.Request) -> web.StreamResponse:
        rlim_window = await _read_ratelimit_window(request)
        if rlim_window is not None and rlim_window.count >= rlim_window.limit:
            return web.HTTPTooManyRequests(
                text=json.dumps({
                    "type": "https://api.backend.ai/probs/rate-limit-exceeded",
                    "title": "You have reached your API query rate limit.",
                }),
                content_type="application/problem+json",
                headers={
                    "X-RateLimit-Limit": str(rlim_window.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rlim_window.reset_after_seconds),
                    "X-RateLimit-Window": str(_RATELIMIT_WINDOW),
                },
            )
        return await handler(request)

    return rlim_handler
