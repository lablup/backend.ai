"""New-style ratelimit module.

This module does not register any routes — it only provides the
``rlim_middleware`` global middleware for rate-limiting authorized
requests.  The middleware and its supporting ``PrivateContext`` are
exposed here so that ``server.py`` can reference them from a single
canonical location.
"""

from __future__ import annotations

from ai.backend.manager.api.rest.routing import RouteRegistry


def register_routes(
    registry: RouteRegistry,
) -> None:
    """No routes to register — ratelimit is middleware-only."""
