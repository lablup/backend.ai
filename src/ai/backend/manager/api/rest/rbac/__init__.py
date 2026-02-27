"""New-style RBAC module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import RBACHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register RBAC routes on the given RouteRegistry."""
    handler = RBACHandler(processors=processors)

    # Role management routes
    registry.add("POST", "/admin/rbac/roles", handler.create_role, middlewares=[auth_required])
    registry.add(
        "POST", "/admin/rbac/roles/search", handler.search_roles, middlewares=[auth_required]
    )
    registry.add(
        "GET", "/admin/rbac/roles/{role_id}", handler.get_role, middlewares=[auth_required]
    )
    registry.add(
        "PATCH", "/admin/rbac/roles/{role_id}", handler.update_role, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/admin/rbac/roles/delete", handler.delete_role, middlewares=[auth_required]
    )
    registry.add("POST", "/admin/rbac/roles/purge", handler.purge_role, middlewares=[auth_required])

    # Role assignment routes
    registry.add(
        "POST", "/admin/rbac/roles/assign", handler.assign_role, middlewares=[auth_required]
    )
    registry.add(
        "POST", "/admin/rbac/roles/revoke", handler.revoke_role, middlewares=[auth_required]
    )
    registry.add(
        "POST",
        "/admin/rbac/roles/{role_id}/assigned-users/search",
        handler.search_assigned_users,
        middlewares=[auth_required],
    )

    # Scope routes
    registry.add(
        "GET", "/admin/rbac/scope-types", handler.get_scope_types, middlewares=[auth_required]
    )
    registry.add(
        "POST",
        "/admin/rbac/scopes/{scope_type}/search",
        handler.search_scopes,
        middlewares=[auth_required],
    )

    # Entity routes
    registry.add(
        "GET", "/admin/rbac/entity-types", handler.get_entity_types, middlewares=[auth_required]
    )
    registry.add(
        "POST",
        "/admin/rbac/scopes/{scope_type}/{scope_id}/entities/{entity_type}/search",
        handler.search_entities,
        middlewares=[auth_required],
    )
