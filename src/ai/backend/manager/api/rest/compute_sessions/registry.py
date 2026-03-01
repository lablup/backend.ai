"""Compute sessions module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ComputeSessionsHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_compute_sessions_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the compute sessions sub-application."""
    reg = RouteRegistry.create("compute-sessions", deps.cors_options)
    if deps.processors is None:
        raise RuntimeError("processors is required for compute_sessions module")
    handler = ComputeSessionsHandler(processors=deps.processors)

    reg.add(
        "POST",
        "/search",
        handler.search_sessions,
        middlewares=[superadmin_required, server_status_required(ALL_ALLOWED)],
    )
    return reg
