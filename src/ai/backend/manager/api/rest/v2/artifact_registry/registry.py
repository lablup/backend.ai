"""Route registry for REST v2 artifact registry endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ArtifactRegistryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_artifact_registry_routes(
    handler: V2ArtifactRegistryHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 artifact registry routes and return the sub-registry."""
    registry = RouteRegistry.create("artifact-registries", route_deps.cors_options)

    registry.add(
        "GET",
        "/{registry_id}",
        handler.get_registry_meta,
        middlewares=[auth_required],
    )

    return registry
