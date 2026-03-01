from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_user_routes

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.config.unified import AuthConfig
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_user_routes"]


def register_routes(
    registry: RouteRegistry, processors: Processors, auth_config: AuthConfig
) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_user_routes`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import superadmin_required

    from .handler import UserHandler

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
