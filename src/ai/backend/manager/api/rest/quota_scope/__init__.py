"""New-style quota_scope module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import QuotaScopeHandler

if TYPE_CHECKING:
    from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager


def register_routes(
    registry: RouteRegistry,
    storage_manager: StorageSessionManager,
) -> None:
    """Register quota scope routes on the given RouteRegistry."""
    handler = QuotaScopeHandler(storage_manager=storage_manager)

    _mw = [auth_required, superadmin_required]

    registry.add(
        "GET",
        "/admin/quota-scopes/{storage_host_name}/{quota_scope_id}",
        handler.get,
        middlewares=_mw,
    )
    registry.add("POST", "/admin/quota-scopes/search", handler.search, middlewares=_mw)
    registry.add("POST", "/admin/quota-scopes/set", handler.set_quota, middlewares=_mw)
    registry.add("POST", "/admin/quota-scopes/unset", handler.unset_quota, middlewares=_mw)
