"""Per-user rate limiting for requests proxied to the manager.

Reads the window the manager-side limiter (``manager/api/rest/ratelimit``) keeps per
user; only the manager counts, ``manager_proxy_rate_limited()`` rejects when the count
has already reached the limit. Without an open window, or one without a limit, the
request is proxied and the manager alone limits it.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Final

from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.web.session import get_session
from ai.backend.logging import BraceStyleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_RATELIMIT_WINDOW: Final = 60 * 15

type Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


def manager_proxy_rate_limited(handler: Handler) -> Handler:
    """Wrap a manager proxy handler so the web server rejects over-limit requests."""

    async def rlim_handler(request: web.Request) -> web.StreamResponse:
        session = await get_session(request)
        if not session.get("authenticated", False):
            return await handler(request)
        token = session.get("token") or {}
        raw_user_id = token.get("user_id")
        if raw_user_id is None:
            # A session stored before the login handler started keeping the user id.
            return await handler(request)
        user_id = UserID(uuid.UUID(raw_user_id))

        valkey_client: ValkeyRateLimitClient = request.app["valkey_rate_limit"]
        state = await valkey_client.get_state(user_id)
        if state is None or state.limit is None:
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
                    "X-RateLimit-Reset": str(state.reset),
                    "X-RateLimit-Window": str(_RATELIMIT_WINDOW),
                },
            )
        return await handler(request)

    return rlim_handler
