"""Route registry for REST v2 artifact endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ArtifactHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_artifact_routes(
    handler: V2ArtifactHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 artifact routes and return the sub-registry."""
    registry = RouteRegistry.create("artifacts", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.admin_search,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{artifact_id}",
        handler.get,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{artifact_id}",
        handler.update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/delete",
        handler.delete,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/restore",
        handler.restore,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/revisions/{revision_id}",
        handler.get_revision,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/revisions/{revision_id}/approve",
        handler.approve_revision,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/revisions/{revision_id}/reject",
        handler.reject_revision,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/revisions/{revision_id}/cancel-import",
        handler.cancel_import,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/revisions/{revision_id}/cleanup",
        handler.cleanup_revision,
        middlewares=[superadmin_required],
    )

    return registry
