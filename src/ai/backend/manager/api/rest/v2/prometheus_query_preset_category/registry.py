"""Route registration for v2 prometheus query preset category endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2PrometheusQueryPresetCategoryHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_prometheus_query_preset_category_routes(
    handler: V2PrometheusQueryPresetCategoryHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 prometheus query preset category routes.

    Create is restricted to superadmins; the rest check the caller's permission on
    each category.
    """
    reg = RouteRegistry.create("prometheus-query-preset-categories", route_deps.cors_options)

    reg.add("POST", "", handler.create, middlewares=[superadmin_required])
    reg.add("POST", "/search", handler.search, middlewares=[auth_required])
    reg.add("GET", "/{category_id}", handler.get, middlewares=[auth_required])
    reg.add("DELETE", "/{category_id}", handler.purge, middlewares=[auth_required])
    reg.add("POST", "/partial-bulk-purge", handler.partial_bulk_purge, middlewares=[auth_required])
    # Deprecated since NEXT_RELEASE_VERSION.
    reg.add("POST", "/delete", handler.delete, middlewares=[superadmin_required])

    return reg
