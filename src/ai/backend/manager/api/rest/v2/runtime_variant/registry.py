"""Route registry for REST v2 runtime variant endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2RuntimeVariantHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_runtime_variant_routes(
    handler: V2RuntimeVariantHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    registry = RouteRegistry.create("runtime-variants", route_deps.cors_options)

    registry.add(
        "POST",
        "/search",
        handler.search,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "",
        handler.create,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{variant_id}",
        handler.get,
        middlewares=[auth_required],
    )
    registry.add(
        "PATCH",
        "/{variant_id}",
        handler.update,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/{variant_id}",
        handler.delete,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/delete",
        handler.bulk_delete,
        middlewares=[superadmin_required],
    )

    return registry
