"""Health module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import HealthHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_health_routes(
    handler: HealthHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Build the public health sub-application.

    Three routes under the ``/health`` prefix:

    - ``/health`` (no path suffix) — minimal liveness payload with the
      Manager version. Public-facing, no internal connectivity is exposed.
    - ``/health/livez`` and ``/health/readyz`` — status-only K8s-style
      probes that mirror the internal liveness / readiness tiers but omit
      the response body so the per-component matrix never leaks externally.
    """
    reg = RouteRegistry.create("health", route_deps.cors_options)

    # Public endpoints — no auth required
    reg.add("GET", "", handler.hello)
    reg.add("GET", "/livez", handler.livez)
    reg.add("GET", "/readyz", handler.readyz)

    return reg
