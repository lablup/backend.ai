"""Route registry for REST v2 fair share endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2FairShareHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_fair_share_routes(
    handler: V2FairShareHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 fair share routes and return the sub-registry."""
    registry = RouteRegistry.create("fair-share", route_deps.cors_options)

    # Domain fair share
    registry.add(
        "POST",
        "/domains/get",
        handler.admin_get_domain,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/domains/search",
        handler.admin_search_domain,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/domains/upsert",
        handler.admin_upsert_domain,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/domains/bulk-upsert",
        handler.admin_bulk_upsert_domain,
        middlewares=[superadmin_required],
    )

    # Project fair share
    registry.add(
        "POST",
        "/projects/get",
        handler.admin_get_project,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/projects/search",
        handler.admin_search_project,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/projects/upsert",
        handler.admin_upsert_project,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/projects/bulk-upsert",
        handler.admin_bulk_upsert_project,
        middlewares=[superadmin_required],
    )

    # User fair share
    registry.add(
        "POST",
        "/users/get",
        handler.admin_get_user,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/users/search",
        handler.admin_search_user,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/users/upsert",
        handler.admin_upsert_user,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/users/bulk-upsert",
        handler.admin_bulk_upsert_user,
        middlewares=[superadmin_required],
    )

    return registry
