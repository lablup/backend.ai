"""Ratelimit module registrar.

The ValkeyRateLimitClient lifecycle (init/shutdown) is managed by the
DependencyComposer infrastructure layer (``ValkeyDependency``).  This
registry only wires the pre-created client into the sub-application
context for the ``rlim_middleware`` to use.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


def register_ratelimit_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the ratelimit sub-application.

    This module does not register any routes -- it only provides the
    ``rlim_middleware`` global middleware for rate-limiting authorized
    requests.
    """
    from .handler import make_rlim_middleware

    reg = RouteRegistry.create("ratelimit", deps.cors_options)

    if deps.valkey_rate_limit is not None:
        reg.rlim_middleware = make_rlim_middleware(deps.valkey_rate_limit)

    return reg
