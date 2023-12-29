from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import Final, Iterable, Tuple

import attrs
from aiohttp import web
from aiotools import apartial

from ai.backend.common import redis_helper
from ai.backend.common.defs import REDIS_RLIM_DB
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import RedisConnectionInfo

from .context import RootContext
from .exceptions import RateLimitExceeded
from .types import CORSOptions, WebMiddleware, WebRequestHandler

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

_time_prec: Final = Decimal("1e-3")  # msec
_rlim_window: Final = 60 * 15

# We implement rate limiting using a rolling counter, which prevents
# last-minute and first-minute bursts between the intervals.

_rlim_script = """
local access_key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local request_id = tonumber(redis.call('INCR', '__request_id'))
if request_id >= 1e12 then
    redis.call('SET', '__request_id', 1)
end
if redis.call('EXISTS', access_key) == 1 then
    redis.call('ZREMRANGEBYSCORE', access_key, 0, now - window)
end
redis.call('ZADD', access_key, now, tostring(request_id))
redis.call('EXPIRE', access_key, window)
return redis.call('ZCARD', access_key)
"""


@web.middleware
async def rlim_middleware(
    app: web.Application,
    request: web.Request,
    handler: WebRequestHandler,
) -> web.StreamResponse:
    # This is a global middleware: request.app is the root app.
    app_ctx: PrivateContext = app["ratelimit.context"]
    now = Decimal(time.time()).quantize(_time_prec)
    rr = app_ctx.redis_rlim
    if request["is_authorized"]:
        rate_limit = request["keypair"]["rate_limit"]
        access_key = request["keypair"]["access_key"]
        ret = await redis_helper.execute_script(
            rr,
            "ratelimit",
            _rlim_script,
            [access_key],
            [str(now), str(_rlim_window)],
        )
        if ret is None:
            remaining = rate_limit
        else:
            rolling_count = int(ret)
            if rate_limit is not None and rolling_count > rate_limit:
                raise RateLimitExceeded
            remaining = rate_limit - rolling_count
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
    redis_rlim: RedisConnectionInfo
    redis_rlim_script: str


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: PrivateContext = app["ratelimit.context"]
    app_ctx.redis_rlim = redis_helper.get_redis_object(
        root_ctx.shared_config.data["redis"], name="ratelimit", db=REDIS_RLIM_DB
    )
    app_ctx.redis_rlim_script = await redis_helper.execute(
        app_ctx.redis_rlim, lambda r: r.script_load(_rlim_script)
    )


async def shutdown(app: web.Application) -> None:
    app_ctx: PrivateContext = app["ratelimit.context"]
    await redis_helper.execute(app_ctx.redis_rlim, lambda r: r.flushdb())
    await app_ctx.redis_rlim.close()


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4)
    app["ratelimit.context"] = PrivateContext()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    # middleware must be wrapped by web.middleware at the outermost level.
    return app, [web.middleware(apartial(rlim_middleware, app))]
