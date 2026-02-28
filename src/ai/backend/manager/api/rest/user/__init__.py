"""New-style user module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import UserHandler

if TYPE_CHECKING:
    from ai.backend.manager.config.unified import AuthConfig
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
    auth_config: AuthConfig,
) -> None:
    """Register user admin routes on the given RouteRegistry."""
    handler = UserHandler(processors=processors, auth_config=auth_config)

    registry.add("POST", "", handler.create_user, middlewares=[superadmin_required])
    registry.add(
        "GET",
        r"/{user_id}",
        handler.get_user,
        middlewares=[superadmin_required],
    )
    registry.add("POST", "/search", handler.search_users, middlewares=[superadmin_required])
    registry.add(
        "PATCH",
        r"/{user_id}",
        handler.update_user,
        middlewares=[superadmin_required],
    )
    registry.add("POST", "/delete", handler.delete_user, middlewares=[superadmin_required])
    registry.add("POST", "/purge", handler.purge_user, middlewares=[superadmin_required])
