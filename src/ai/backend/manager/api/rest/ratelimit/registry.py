"""Ratelimit module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_ratelimit_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the ratelimit sub-application.

    This module does not register any routes -- it only provides the
    ``rlim_middleware`` global middleware for rate-limiting authorized
    requests.  The PrivateContext and lifecycle hooks are wired here so
    that server.py can reference them from a single canonical location.
    """
    from ai.backend.manager.api.ratelimit import (
        PrivateContext as RatelimitPrivateContext,
    )
    from ai.backend.manager.api.ratelimit import (
        init as rlim_init,
    )
    from ai.backend.manager.api.ratelimit import (
        shutdown as rlim_shutdown,
    )

    reg = RouteRegistry.create("ratelimit", deps.cors_options)
    ctx = RatelimitPrivateContext()

    # Store ctx on app dict for backward compatibility (lifecycle functions
    # read from app["ratelimit.context"]).
    reg.app["ratelimit.context"] = ctx

    # Expose ctx on the registry for typed access by server.py when
    # installing rlim_middleware as a root-app middleware.
    reg.ratelimit_ctx = ctx

    # Wire lifecycle hooks
    reg.app.on_startup.append(rlim_init)
    reg.app.on_shutdown.append(rlim_shutdown)

    # No routes to register -- ratelimit is middleware-only.
    return reg
