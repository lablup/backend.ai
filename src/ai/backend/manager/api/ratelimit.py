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
from ai.backend.common.networking import get_client_ip
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
local id_type = KEYS[1]
local id_value = KEYS[2]
local namespaced_id = id_type .. ":" .. id_value
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local request_id = tonumber(redis.call('INCR', '__request_id'))
if request_id >= 1e12 then
    redis.call('SET', '__request_id', 1)
end
if redis.call('EXISTS', namespaced_id) == 1 then
    redis.call('ZREMRANGEBYSCORE', namespaced_id, 0, now - window)
end
redis.call('ZADD', namespaced_id, now, tostring(request_id))
redis.call('EXPIRE', namespaced_id, window)

local rolling_count = redis.call('ZCARD', namespaced_id)

if id_type == "ip" then
    local rate_limit = tonumber(ARGV[3])
    local score_threshold = rate_limit * 0.8

    -- Add IP to suspicious_ips only if count is greater than score_threshold
    if rolling_count >= score_threshold then
        redis.call('ZADD', 'suspicious_ips', rolling_count, id_value)
    end
end

return rolling_count
"""


@web.middleware
async def rlim_middleware(
    app: web.Application,
    request: web.Request,
    handler: WebRequestHandler,
) -> web.StreamResponse:
    # This is a global middleware: request.app is the root app.
    app_ctx: RateLimitContext = app["ratelimit.context"]
    now = Decimal(time.time()).quantize(_time_prec)
    rr = app_ctx.redis_rlim

    if request["is_authorized"]:
        rate_limit = request["keypair"]["rate_limit"]
        access_key = request["keypair"]["access_key"]
        ret = await redis_helper.execute_script(
            rr,
            "ratelimit",
            _rlim_script,
            ["access_key", access_key],
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
        root_ctx: RootContext = app["_root.context"]
        rate_limit = root_ctx.shared_config["anonymous_ratelimit"]

        ip_address = get_client_ip(request)

        if not ip_address or rate_limit is None:
            # No checks for rate limiting.
            response = await handler(request)
            # Arbitrary number for indicating no rate limiting.
            response.headers["X-RateLimit-Limit"] = "1000"
            response.headers["X-RateLimit-Remaining"] = "1000"
        else:
            ret = await redis_helper.execute_script(
                rr,
                "ratelimit",
                _rlim_script,
                ["ip", ip_address],
                [str(now), str(_rlim_window), str(rate_limit)],
            )
            if ret is None:
                remaining = rate_limit
            else:
                rolling_count = int(ret)
                remaining = rate_limit - rolling_count
                if remaining < 0:
                    raise RateLimitExceeded

            response = await handler(request)
            response.headers["X-RateLimit-Limit"] = str(rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)

        response.headers["X-RateLimit-Window"] = str(_rlim_window)
        return response


@attrs.define(slots=True, auto_attribs=True, init=False)
class RateLimitContext:
    redis_rlim: RedisConnectionInfo
    redis_rlim_script: str


async def init(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    app_ctx: RateLimitContext = app["ratelimit.context"]
    app_ctx.redis_rlim = redis_helper.get_redis_object(
        root_ctx.shared_config.data["redis"], name="ratelimit", db=REDIS_RLIM_DB
    )
    app_ctx.redis_rlim_script = await redis_helper.execute(
        app_ctx.redis_rlim, lambda r: r.script_load(_rlim_script)
    )


async def shutdown(app: web.Application) -> None:
    app_ctx: RateLimitContext = app["ratelimit.context"]
    await redis_helper.execute(app_ctx.redis_rlim, lambda r: r.flushdb())
    await app_ctx.redis_rlim.close()


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4)
    app["ratelimit.context"] = RateLimitContext()

    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    # middleware must be wrapped by web.middleware at the outermost level.
    return app, [web.middleware(apartial(rlim_middleware, app))]
