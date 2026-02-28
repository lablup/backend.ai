"""New-style image module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ImageHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
) -> None:
    """Register image routes on the given RouteRegistry."""
    handler = ImageHandler(processors=processors)

    _mw = [auth_required, superadmin_required]

    registry.add("POST", "/admin/images/search", handler.search, middlewares=_mw)
    registry.add("GET", "/admin/images/{image_id}", handler.get, middlewares=_mw)
    registry.add("POST", "/admin/images/rescan", handler.rescan, middlewares=_mw)
    registry.add("POST", "/admin/images/alias", handler.alias, middlewares=_mw)
    registry.add("POST", "/admin/images/dealias", handler.dealias, middlewares=_mw)
    registry.add("POST", "/admin/images/forget", handler.forget, middlewares=_mw)
    registry.add("POST", "/admin/images/purge", handler.purge, middlewares=_mw)
