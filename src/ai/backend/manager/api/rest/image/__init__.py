from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_image_routes

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_image_routes"]


def register_routes(registry: RouteRegistry, processors: Processors) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_image_routes`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required

    from .handler import ImageHandler

    handler = ImageHandler(processors=processors)

    _mw = [auth_required, superadmin_required]

    registry.add("POST", "/search", handler.search, middlewares=_mw)
    registry.add("GET", "/{image_id}", handler.get, middlewares=_mw)
    registry.add("POST", "/rescan", handler.rescan, middlewares=_mw)
    registry.add("POST", "/alias", handler.alias, middlewares=_mw)
    registry.add("POST", "/dealias", handler.dealias, middlewares=_mw)
    registry.add("POST", "/forget", handler.forget, middlewares=_mw)
    registry.add("POST", "/purge", handler.purge, middlewares=_mw)
