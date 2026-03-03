"""Compute sessions module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.server_status import ALL_ALLOWED, server_status_required

from .handler import ComputeSessionsHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_compute_sessions_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the compute sessions sub-application."""
    reg = RouteRegistry.create("compute-sessions", deps.cors_options)
    handler = ComputeSessionsHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/search",
        handler.search_sessions,
        middlewares=[
            superadmin_required,
            server_status_required(ALL_ALLOWED, deps.config_provider),
        ],
    )
    return reg
