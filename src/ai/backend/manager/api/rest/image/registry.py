"""Image sub-registry registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ImageHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_image_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the image sub-registry (child of admin)."""
    reg = RouteRegistry.create("images", deps.cors_options)
    handler = ImageHandler(processors=deps.processors)

    _mw = [auth_required, superadmin_required]

    reg.add("POST", "/search", handler.search, middlewares=_mw)
    reg.add("GET", "/{image_id}", handler.get, middlewares=_mw)
    reg.add("POST", "/rescan", handler.rescan, middlewares=_mw)
    reg.add("POST", "/alias", handler.alias, middlewares=_mw)
    reg.add("POST", "/dealias", handler.dealias, middlewares=_mw)
    reg.add("POST", "/forget", handler.forget, middlewares=_mw)
    reg.add("POST", "/purge", handler.purge, middlewares=_mw)

    return reg
