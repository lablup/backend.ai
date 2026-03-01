from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_acl_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry

__all__ = ["register_acl_module"]


def register_routes(registry: RouteRegistry) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_acl_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.manager import ALL_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import AclHandler

    handler = AclHandler()
    registry.add(
        "GET",
        "",
        handler.get_permission,
        middlewares=[auth_required, server_status_required(ALL_ALLOWED)],
    )
