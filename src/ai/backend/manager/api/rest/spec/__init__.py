"""New-style spec module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import SpecHandler

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    _processors: Processors,
) -> None:
    """Register spec routes on the given RouteRegistry."""
    handler = SpecHandler()

    registry.add(
        "GET",
        "/spec/graphiql",
        handler.render_graphiql_graphene_html,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/spec/graphiql/strawberry",
        handler.render_graphiql_strawberry_html,
    )
    registry.add(
        "GET",
        "/spec/openapi",
        handler.render_openapi_html,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/spec/openapi/spec.json",
        handler.generate_openapi_spec,
        middlewares=[auth_required],
    )
