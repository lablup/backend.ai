"""Route registry for REST v2 model card endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ModelCardHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_model_card_routes(
    handler: V2ModelCardHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    registry = RouteRegistry.create("model-cards", route_deps.cors_options)

    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add(
        "POST",
        "/projects/{project_id}/search",
        handler.project_search,
        middlewares=[auth_required],
    )
    registry.add("POST", "", handler.create, middlewares=[superadmin_required])
    registry.add("GET", "/{card_id}", handler.get, middlewares=[auth_required])
    registry.add("PATCH", "/{card_id}", handler.update, middlewares=[superadmin_required])
    registry.add("DELETE", "/{card_id}", handler.delete, middlewares=[superadmin_required])
    registry.add("POST", "/delete", handler.bulk_delete, middlewares=[superadmin_required])
    registry.add(
        "POST",
        "/projects/{project_id}/scan",
        handler.scan_project,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{card_id}/deploy",
        handler.deploy,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{card_id}/available-presets/search",
        handler.available_presets,
        middlewares=[auth_required],
    )

    return registry
