"""Per-user rate limiting for requests proxied to the manager.

The same rolling counter and limit value as the manager-side rate limiter
(``manager/api/rest/ratelimit``): the limit is the keypair ``rate_limit``
delivered at login (``None`` means unlimited), and the counter is keyed by the
login user, so holding multiple keypairs does not multiply the allowance.
Over-limit requests are rejected with HTTP 429 at the web server, before they
reach the manager.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Final

from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.identifier.user import UserID
from ai.backend.common.web.session import get_session
from ai.backend.logging import BraceStyleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_rlim_window: Final = 60 * 15
_RATE_LIMITED_PATH_PREFIX: Final = "/func/"


@web.middleware
async def rate_limit_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    if not request.path.startswith(_RATE_LIMITED_PATH_PREFIX):
        return await handler(request)
    session = await get_session(request)
    if not session.get("authenticated", False):
        return await handler(request)
    token = session.get("token") or {}
    raw_user_id = token.get("user_id")
    if raw_user_id is None:
        # Session created against a manager that does not send the user ID yet.
        return await handler(request)
    rate_limit = token.get("rate_limit")

    valkey_client: ValkeyRateLimitClient = request.app["valkey_rate_limit"]
    rolling_count = await valkey_client.execute_rate_limit_logic(
        user_id=UserID(uuid.UUID(raw_user_id)),
        window=_rlim_window,
    )
    remaining = max(rate_limit - rolling_count, 0) if rate_limit is not None else rolling_count
    rlim_headers = {
        "X-RateLimit-Limit": str(rate_limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Window": str(_rlim_window),
    }
    if rate_limit is not None and rolling_count > rate_limit:
        return web.HTTPTooManyRequests(
            text=json.dumps({
                "type": "https://api.backend.ai/probs/rate-limit-exceeded",
                "title": "You have reached your API query rate limit.",
            }),
            content_type="application/problem+json",
            headers=rlim_headers,
        )
    response = await handler(request)
    if not response.prepared:
        response.headers.update(rlim_headers)
    return response
