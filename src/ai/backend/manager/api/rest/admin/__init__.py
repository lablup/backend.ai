from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_admin_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_admin_module"]


def register_routes(registry: RouteRegistry, _processors: Processors) -> None:
    """Backward-compatible shim — delegates to the old inline logic.

    The canonical entry-point is :func:`register_admin_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.gql_legacy.schema import graphene_schema
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import AdminHandler

    handler = AdminHandler(gql_schema=graphene_schema)

    registry.add(
        "POST",
        "/graphql",
        handler.handle_gql_legacy,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/gql",
        handler.handle_gql_graphene,
        middlewares=[auth_required],
    )
