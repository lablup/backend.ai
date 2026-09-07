"""Rate limiting for requests proxied to the manager.

Reads the window the manager-side limiter (``manager/api/rest/ratelimit``) keeps, keyed
by user for a signed-in caller and by address for an anonymous one; only the manager
counts, ``manager_proxy_rate_limited()`` rejects when the count has already reached the
limit. Without an open window the request is proxied and the manager alone limits it.

The address is the one this server forwards, so a manager that resolves a different one
(``trusted-proxies`` naming hops in front of it) opens a window this check does not
find: the request is proxied and the manager limits it as before.
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
from ai.backend.common.web.session import get_session
from ai.backend.logging import BraceStyleAdapter
from ai.backend.web.auth import get_client_ip

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_RATELIMIT_WINDOW: Final = 60 * 15

type Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


def manager_proxy_rate_limited(handler: Handler) -> Handler:
    """Wrap a manager proxy handler so the web server rejects over-limit requests."""

    async def rlim_handler(request: web.Request) -> web.StreamResponse:
        valkey_client: ValkeyRateLimitClient = request.app["valkey_rate_limit"]
        state: RateLimitState | None
        session = await get_session(request)
        if session.get("authenticated", False):
            token = session.get("token") or {}
            raw_user_id = token.get("user_id")
            if raw_user_id is None:
                # A session stored before the login handler started keeping the user id.
                # The manager counts this caller by user, which this server cannot name.
                return await handler(request)
            state = await valkey_client.get_user_state(UserID(uuid.UUID(raw_user_id)))
        else:
            client_ip = get_client_ip(request)
            if client_ip is None:
                return await handler(request)
            state = await valkey_client.get_ip_state(client_ip)
        if state is None:
            return await handler(request)

        if state.count >= state.limit:
            return web.HTTPTooManyRequests(
                text=json.dumps({
                    "type": "https://api.backend.ai/probs/rate-limit-exceeded",
                    "title": "You have reached your API query rate limit.",
                }),
                content_type="application/problem+json",
                headers={
                    "X-RateLimit-Limit": str(state.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(state.reset_after_seconds),
                    "X-RateLimit-Window": str(_RATELIMIT_WINDOW),
                },
            )
        return await handler(request)

    return rlim_handler
