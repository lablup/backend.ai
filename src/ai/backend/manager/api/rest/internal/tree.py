"""Build the internal API module tree (composition root).

Called from ``server.py`` to assemble all internal route registries into a
single tree served on the internal address.  All handler construction and
dependency wiring happens here — registrars are pure routing functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.internal.health.handler import InternalHealthHandler
from ai.backend.manager.api.rest.internal.health.registry import register_internal_health_routes
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.common.health_checker.probe import HealthProbe


def build_internal_api_routes(*, health_probe: HealthProbe) -> list[RouteRegistry]:
    """Build the internal API module tree and return all root-level registries.

    This is the composition root for the internal address: all handlers are
    constructed here and passed to pure routing registrar functions.
    """
    handler = InternalHealthHandler(health_probe=health_probe)
    return [
        register_internal_health_routes(handler),
    ]
