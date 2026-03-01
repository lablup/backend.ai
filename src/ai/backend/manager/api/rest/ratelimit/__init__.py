from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_ratelimit_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry

__all__ = ["register_ratelimit_module"]


def register_routes(registry: RouteRegistry) -> None:
    """Backward-compatible shim -- no routes to register.

    The canonical entry-point is :func:`register_ratelimit_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.

    Ratelimit is middleware-only; there are no routes.
    """
