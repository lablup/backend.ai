"""Backward-compatibility shim for the ratelimit module.

The rate-limit middleware logic has been migrated to:

* ``api.rest.ratelimit.handler`` — ``rlim_middleware``

This module keeps ``create_app()`` with the ``PrivateContext`` and
Valkey client init/shutdown so that the existing server bootstrap
continues to work.  The ``rlim_middleware`` is re-imported from the new
location and re-exported for backward compatibility.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

import attrs
from aiohttp import web
from aiotools import apartial

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.defs import REDIS_RATE_LIMIT_DB, RedisRole
from ai.backend.logging import BraceStyleAdapter

from .context import RootContext
from .rest.ratelimit.handler import rlim_middleware
from .types import CORSOptions, WebMiddleware

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
    _default_cors_options: CORSOptions,
) -> tuple[web.Application, Iterable[WebMiddleware]]:
    # default_cors_options is kept for API consistency but not used in rate limiting
    app = web.Application()
    app["api_versions"] = (1, 2, 3, 4)
    app["ratelimit.context"] = PrivateContext()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    # middleware must be wrapped by web.middleware at the outermost level.
    return app, [web.middleware(apartial(rlim_middleware, app))]
