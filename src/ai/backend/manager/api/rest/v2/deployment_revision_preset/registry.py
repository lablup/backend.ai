"""Route registry for REST v2 deployment revision preset endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2DeploymentRevisionPresetHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_deployment_revision_preset_routes(
    handler: V2DeploymentRevisionPresetHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    registry = RouteRegistry.create("deployments/revision-presets", route_deps.cors_options)

    registry.add("POST", "/search", handler.search, middlewares=[auth_required])
    registry.add("POST", "", handler.create, middlewares=[superadmin_required])
    registry.add("GET", "/{preset_id}", handler.get, middlewares=[auth_required])
    registry.add("PATCH", "/{preset_id}", handler.update, middlewares=[superadmin_required])
    registry.add("DELETE", "/{preset_id}", handler.delete, middlewares=[superadmin_required])
    registry.add(
        "POST",
        "/{preset_id}/resource-slots/search",
        handler.search_resource_slots,
        middlewares=[auth_required],
    )

    return registry
