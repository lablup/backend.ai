"""Ratelimit module registrar.

Lifecycle management (Valkey rate-limit client init/shutdown) is handled
directly here instead of the legacy ``api.ratelimit`` shim.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

import attrs
from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.defs import REDIS_RATE_LIMIT_DB, RedisRole
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext
    from ai.backend.manager.api.rest.types import ModuleDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


@attrs.define(slots=True, auto_attribs=True, init=False)
class RatelimitContext:
    valkey_rate_limit_client: ValkeyRateLimitClient
    redis_rlim_script: str


async def _ratelimit_startup(app: web.Application) -> None:
    root_ctx: RootContext = app["_root.context"]
    ctx: RatelimitContext = app["ratelimit.context"]
    valkey_profile_target = root_ctx.config_provider.config.redis.to_valkey_profile_target()
    valkey_target = valkey_profile_target.profile_target(RedisRole.RATE_LIMIT)
    ctx.valkey_rate_limit_client = await ValkeyRateLimitClient.create(
        valkey_target=valkey_target,
        db_id=REDIS_RATE_LIMIT_DB,
        human_readable_name="ratelimit",
    )
    # Note: Script functionality is now handled internally by the client
    ctx.redis_rlim_script = ""


async def _ratelimit_shutdown(app: web.Application) -> None:
    ctx: RatelimitContext = app["ratelimit.context"]
    await ctx.valkey_rate_limit_client.flush_database()
    await ctx.valkey_rate_limit_client.close()


def register_ratelimit_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the ratelimit sub-application.

    This module does not register any routes -- it only provides the
    ``rlim_middleware`` global middleware for rate-limiting authorized
    requests.  The ``RatelimitContext`` and lifecycle hooks are managed
    directly here.
    """
    reg = RouteRegistry.create("ratelimit", deps.cors_options)
    ctx = RatelimitContext()

    # Store ctx on app dict for the rlim_middleware handler to read.
    reg.app["ratelimit.context"] = ctx

    # Expose ctx on the registry for typed access by server.py when
    # installing rlim_middleware as a root-app middleware.
    reg.ratelimit_ctx = ctx

    # Wire lifecycle hooks
    reg.app.on_startup.append(_ratelimit_startup)
    reg.app.on_shutdown.append(_ratelimit_shutdown)

    # No routes to register -- ratelimit is middleware-only.
    return reg
