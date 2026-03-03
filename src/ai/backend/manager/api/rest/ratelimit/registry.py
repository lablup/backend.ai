"""Ratelimit module registrar.

The ValkeyRateLimitClient lifecycle (init/shutdown) is managed by the
DependencyComposer infrastructure layer (``ValkeyDependency``).  This
registry only wires the pre-created client into the sub-application
context for the ``rlim_middleware`` to use.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

import attrs

from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


@attrs.define(slots=True, auto_attribs=True)
class RatelimitContext:
    valkey_rate_limit_client: ValkeyRateLimitClient
    redis_rlim_script: str = ""


def register_ratelimit_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the ratelimit sub-application.

    This module does not register any routes -- it only provides the
    ``rlim_middleware`` global middleware for rate-limiting authorized
    requests.  The ``RatelimitContext`` is populated from the pre-created
    ValkeyRateLimitClient injected via ``ModuleDeps``.
    """
    reg = RouteRegistry.create("ratelimit", deps.cors_options)

    if deps.valkey_rate_limit is not None:
        ctx = RatelimitContext(valkey_rate_limit_client=deps.valkey_rate_limit)
        reg.app["ratelimit.context"] = ctx
        reg.ratelimit_ctx = ctx

    return reg
