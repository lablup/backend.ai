"""Quota scope sub-registry registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import QuotaScopeHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_quota_scope_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the quota-scope sub-registry (child of admin)."""
    reg = RouteRegistry.create("quota-scopes", deps.cors_options)
    if deps.storage_manager is None:
        raise RuntimeError("storage_manager is required for quota_scope module")
    handler = QuotaScopeHandler(storage_manager=deps.storage_manager)

    _mw = [auth_required, superadmin_required]

    reg.add(
        "GET",
        "/{storage_host_name}/{quota_scope_id}",
        handler.get,
        middlewares=_mw,
    )
    reg.add("POST", "/search", handler.search, middlewares=_mw)
    reg.add("POST", "/set", handler.set_quota, middlewares=_mw)
    reg.add("POST", "/unset", handler.unset_quota, middlewares=_mw)

    return reg
