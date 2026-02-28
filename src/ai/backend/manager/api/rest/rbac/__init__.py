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
    registry.add("POST", "/roles", handler.create_role, middlewares=[auth_required])
    registry.add("POST", "/roles/search", handler.search_roles, middlewares=[auth_required])
    registry.add("GET", "/roles/{role_id}", handler.get_role, middlewares=[auth_required])
    registry.add("PATCH", "/roles/{role_id}", handler.update_role, middlewares=[auth_required])
    registry.add("POST", "/roles/delete", handler.delete_role, middlewares=[auth_required])
    registry.add("POST", "/roles/purge", handler.purge_role, middlewares=[auth_required])

    # Role assignment routes
    registry.add("POST", "/roles/assign", handler.assign_role, middlewares=[auth_required])
    registry.add("POST", "/roles/revoke", handler.revoke_role, middlewares=[auth_required])
    registry.add(
        "POST",
        "/roles/{role_id}/assigned-users/search",
        handler.search_assigned_users,
        middlewares=[auth_required],
    )

    # Scope routes
    registry.add("GET", "/scope-types", handler.get_scope_types, middlewares=[auth_required])
    registry.add(
        "POST",
        "/scopes/{scope_type}/search",
        handler.search_scopes,
        middlewares=[auth_required],
    )

    # Entity routes
    registry.add("GET", "/entity-types", handler.get_entity_types, middlewares=[auth_required])
    registry.add(
        "POST",
        "/scopes/{scope_type}/{scope_id}/entities/{entity_type}/search",
        handler.search_entities,
        middlewares=[auth_required],
    )
