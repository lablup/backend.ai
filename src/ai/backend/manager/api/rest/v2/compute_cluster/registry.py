"""Route registry for REST v2 compute cluster endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.v2.compute_cluster.handler import V2ComputeClusterHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_compute_cluster_routes(
    handler: V2ComputeClusterHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 compute cluster routes (superadmin only).

    Layout:
        POST   /            create
        POST   /search      search with filter/order/pagination
        GET    /{id}        get by id
        PATCH  /{id}        update
        DELETE /{id}        purge
    """
    registry = RouteRegistry.create("compute-clusters", route_deps.cors_options)

    registry.add("POST", "/", handler.admin_create, middlewares=[superadmin_required])
    registry.add("POST", "/search", handler.admin_search, middlewares=[superadmin_required])
    registry.add(
        "GET",
        "/{compute_cluster_id}",
        handler.admin_get,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/{compute_cluster_id}",
        handler.admin_update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/{compute_cluster_id}",
        handler.admin_purge,
        middlewares=[superadmin_required],
    )

    return registry
