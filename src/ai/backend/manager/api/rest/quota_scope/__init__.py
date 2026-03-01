from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_quota_scope_routes

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager

__all__ = ["register_quota_scope_routes"]


def register_routes(registry: RouteRegistry, storage_manager: StorageSessionManager) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_quota_scope_routes`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required

    from .handler import QuotaScopeHandler

    handler = QuotaScopeHandler(storage_manager=storage_manager)

    _mw = [auth_required, superadmin_required]

    registry.add(
        "GET",
        "/{storage_host_name}/{quota_scope_id}",
        handler.get,
        middlewares=_mw,
    )
    registry.add("POST", "/search", handler.search, middlewares=_mw)
    registry.add("POST", "/set", handler.set_quota, middlewares=_mw)
    registry.add("POST", "/unset", handler.unset_quota, middlewares=_mw)
