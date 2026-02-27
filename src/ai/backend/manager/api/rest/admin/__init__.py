"""New-style admin module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.gql_legacy.schema import graphene_schema
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AdminHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    _processors: Processors,
) -> None:
    """Register admin routes on the given RouteRegistry."""
    handler = AdminHandler(gql_schema=graphene_schema)

    registry.add(
        "POST",
        "/admin/graphql",
        handler.handle_gql_legacy,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/admin/gql",
        handler.handle_gql_graphene,
        middlewares=[auth_required],
    )
