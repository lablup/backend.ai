"""Route registration for v2 prometheus query preset endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2PrometheusQueryPresetHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_prometheus_query_preset_routes(
    handler: V2PrometheusQueryPresetHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 prometheus query preset routes."""
    reg = RouteRegistry.create("prometheus-query-presets", route_deps.cors_options)

    reg.add("POST", "", handler.create, middlewares=[superadmin_required])
    reg.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    reg.add("GET", "/{preset_id}", handler.get, middlewares=[superadmin_required])
    reg.add("PATCH", "/{preset_id}", handler.update, middlewares=[superadmin_required])
    reg.add("POST", "/{preset_id}/execute", handler.execute, middlewares=[superadmin_required])
    reg.add("POST", "/delete", handler.delete, middlewares=[superadmin_required])

    return reg
