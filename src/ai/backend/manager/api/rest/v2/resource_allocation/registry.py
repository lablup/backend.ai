"""Route registry for REST v2 resource allocation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2ResourceAllocationHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_resource_allocation_routes(
    handler: V2ResourceAllocationHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 resource allocation routes and return the sub-registry."""
    registry = RouteRegistry.create("resource-allocation", route_deps.cors_options)

    registry.add(
        "GET",
        "/keypair/my",
        handler.my_keypair_usage,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/projects/{project_id}",
        handler.project_usage,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/domains/{domain_name}",
        handler.admin_domain_usage,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/resource-groups/{name}",
        handler.resource_group_usage,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/effective",
        handler.effective_allocation,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/admin/effective",
        handler.admin_effective_allocation,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/check-preset-availability",
        handler.check_preset_availability,
        middlewares=[auth_required],
    )

    return registry
