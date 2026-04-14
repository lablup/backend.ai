"""Route registry for REST v2 login client type endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2LoginClientTypeHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_login_client_type_routes(
    handler: V2LoginClientTypeHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 login client type routes and return the sub-registry.

    Layout:
        POST   /            create (superadmin only)
        POST   /search      search with filter/order/pagination (authenticated users)
        GET    /{id}        get by id (authenticated users)
        PATCH  /{id}        update (superadmin only)
        DELETE /{id}        delete (superadmin only)
    """
    registry = RouteRegistry.create("login-client-types", route_deps.cors_options)

    registry.add(
        "POST",
        "/",
        handler.admin_create,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/search",
        handler.search,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/{login_client_type_id}",
        handler.get,
        middlewares=[auth_required],
    )
    registry.add(
        "PATCH",
        "/{login_client_type_id}",
        handler.admin_update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/{login_client_type_id}",
        handler.admin_delete,
        middlewares=[superadmin_required],
    )

    return registry
