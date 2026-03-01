from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_spec_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry
    from ai.backend.manager.services.processors import Processors

__all__ = ["register_spec_module"]


def register_routes(registry: RouteRegistry, _processors: Processors | None = None) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_spec_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import auth_required

    from .handler import SpecHandler

    handler = SpecHandler()

    registry.add(
        "GET",
        "/graphiql",
        handler.render_graphiql_graphene_html,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/graphiql/strawberry",
        handler.render_graphiql_strawberry_html,
    )
    registry.add(
        "GET",
        "/openapi",
        handler.render_openapi_html,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/openapi/spec.json",
        handler.generate_openapi_spec,
        middlewares=[auth_required],
    )
