"""New-style deployment module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import DeploymentAPIHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register deployment routes on the given RouteRegistry."""
    handler = DeploymentAPIHandler(processors=processors)

    # Deployment routes
    registry.add("POST", "/", handler.create_deployment, middlewares=[auth_required])
    registry.add("POST", "/search", handler.search_deployments, middlewares=[auth_required])
    registry.add("GET", "/{deployment_id}", handler.get_deployment, middlewares=[auth_required])
    registry.add(
        "PATCH",
        "/{deployment_id}",
        handler.update_deployment,
        middlewares=[auth_required],
    )
    registry.add(
        "DELETE",
        "/{deployment_id}",
        handler.destroy_deployment,
        middlewares=[auth_required],
    )

    # Revision routes (nested under deployment)
    registry.add(
        "POST",
        "/{deployment_id}/revisions/search",
        handler.search_revisions,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/{deployment_id}/revisions/{revision_id}",
        handler.get_revision,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{deployment_id}/revisions/{revision_id}/activate",
        handler.activate_revision,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{deployment_id}/revisions/{revision_id}/deactivate",
        handler.deactivate_revision,
        middlewares=[auth_required],
    )

    # Route routes (nested under deployment)
    registry.add(
        "POST",
        "/{deployment_id}/routes/search",
        handler.search_routes,
        middlewares=[auth_required],
    )
    registry.add(
        "PATCH",
        "/{deployment_id}/routes/{route_id}/traffic-status",
        handler.update_route_traffic_status,
        middlewares=[auth_required],
    )
