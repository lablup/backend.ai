"""Route registry for REST v2 role invitation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2RoleInvitationHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_role_invitation_routes(
    handler: V2RoleInvitationHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 role invitation routes."""
    registry = RouteRegistry.create("role-invitations", route_deps.cors_options)

    # Create invitation (admin)
    registry.add(
        "POST",
        "",
        handler.create,
        middlewares=[auth_required],
    )
    # Accept invitation (invitee)
    registry.add(
        "POST",
        "/{invitation_id}/accept",
        handler.accept,
        middlewares=[auth_required],
    )
    # Reject invitation (invitee)
    registry.add(
        "POST",
        "/{invitation_id}/reject",
        handler.reject,
        middlewares=[auth_required],
    )
    # Cancel invitation (admin)
    registry.add(
        "DELETE",
        "/{invitation_id}",
        handler.cancel,
        middlewares=[auth_required],
    )
    # Search own invitations (invitee)
    registry.add(
        "POST",
        "/my/search",
        handler.my_search,
        middlewares=[auth_required],
    )
    # Search invitations sent by the current user (inviter)
    registry.add(
        "POST",
        "/my/sent-search",
        handler.my_sent_search,
        middlewares=[auth_required],
    )
    # Search invitations by role (scoped — non-admin with role permission also allowed)
    registry.add(
        "POST",
        "/roles/{role_id}/search",
        handler.role_search,
        middlewares=[auth_required],
    )
    # Search all invitations across the system (superadmin only)
    registry.add(
        "POST",
        "/search",
        handler.admin_search,
        middlewares=[superadmin_required],
    )

    return registry
