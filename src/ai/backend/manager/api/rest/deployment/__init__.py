from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_deployment_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_deployment_module"]


def register_routes(registry: RouteRegistry, processors: Processors) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_deployment_module`; this
    wrapper exists only so that ``server.py`` keeps working until it is
    migrated to the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import DeploymentAPIHandler

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
