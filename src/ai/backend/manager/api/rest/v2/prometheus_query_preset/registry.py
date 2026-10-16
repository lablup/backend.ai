"""Route registration for v2 prometheus query preset endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2PrometheusQueryPresetHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_prometheus_query_preset_routes(
    handler: V2PrometheusQueryPresetHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all v2 prometheus query preset routes.

    Create and preview are restricted to superadmins; the rest check the caller's
    permission on each preset.
    """
    reg = RouteRegistry.create("prometheus-query-presets", route_deps.cors_options)

    reg.add("POST", "", handler.create, middlewares=[superadmin_required])
    reg.add("POST", "/search", handler.search, middlewares=[auth_required])
    reg.add("POST", "/preview", handler.admin_preview, middlewares=[superadmin_required])
    reg.add("GET", "/{preset_id}", handler.get, middlewares=[auth_required])
    reg.add("PATCH", "/{preset_id}", handler.update, middlewares=[auth_required])
    reg.add("POST", "/{preset_id}/execute", handler.execute, middlewares=[auth_required])
    reg.add("DELETE", "/{preset_id}", handler.purge, middlewares=[auth_required])
    reg.add(
        "POST", "/partial-bulk-update", handler.partial_bulk_update, middlewares=[auth_required]
    )
    reg.add("POST", "/partial-bulk-purge", handler.partial_bulk_purge, middlewares=[auth_required])
    # Deprecated since NEXT_RELEASE_VERSION.
    reg.add("POST", "/delete", handler.delete, middlewares=[superadmin_required])

    return reg
