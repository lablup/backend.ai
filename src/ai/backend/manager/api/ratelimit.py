from __future__ import annotations

import logging
from typing import Final, Iterable, Tuple

import attrs
from aiohttp import web
from aiotools import apartial

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.defs import REDIS_RATE_LIMIT_DB, RedisRole
from ai.backend.logging import BraceStyleAdapter

from ..errors.api import RateLimitExceeded
from .context import RootContext
from .types import CORSOptions, WebMiddleware, WebRequestHandler

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_rlim_window: Final = 60 * 15

# We implement rate limiting using a rolling counter, which prevents
# last-minute and first-minute bursts between the intervals.


@web.middleware
async def rlim_middleware(
    app: web.Application,
    request: web.Request,
    handler: WebRequestHandler,
) -> web.StreamResponse:
    # This is a global middleware: request.app is the root app.
    app_ctx: PrivateContext = app["ratelimit.context"]
    if request["is_authorized"]:
        rate_limit = request["keypair"]["rate_limit"]
        access_key = request["keypair"]["access_key"]
        rolling_count = await app_ctx.valkey_rate_limit_client.execute_rate_limit_logic(
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
    else:
        # No checks for rate limiting for non-authorized queries.
        response = await handler(request)
        response.headers["X-RateLimit-Limit"] = "1000"
        response.headers["X-RateLimit-Remaining"] = "1000"
        response.headers["X-RateLimit-Window"] = str(_rlim_window)
        return response


@attrs.define(slots=True, auto_attribs=True, init=False)
class PrivateContext:
    valkey_rate_limit_client: ValkeyRateLimitClient
    redis_rlim_script: str


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["ratelimit.context"]
    valkey_profile_target = root_ctx.config_provider.config.redis.to_valkey_profile_target()
    valkey_target = valkey_profile_target.profile_target(RedisRole.RATE_LIMIT)
    app_ctx.valkey_rate_limit_client = await ValkeyRateLimitClient.create(
        valkey_target=valkey_target,
        db_id=REDIS_RATE_LIMIT_DB,
        human_readable_name="ratelimit",
    )
    # Note: Script functionality is now handled internally by the client
    app_ctx.redis_rlim_script = ""


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["ratelimit.context"]
    await app_ctx.valkey_rate_limit_client.flush_database()
    await app_ctx.valkey_rate_limit_client.close()


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    # default_cors_options is kept for API consistency but not used in rate limiting
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4)
    app["ratelimit.context"] = PrivateContext()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    # middleware must be wrapped by web.middleware at the outermost level.
    return app, [web.middleware(apartial(rlim_middleware, app))]
