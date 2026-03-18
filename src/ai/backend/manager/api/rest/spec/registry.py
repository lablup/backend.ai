"""Spec module registrar.

The lifecycle hook (previously in ``api.spec.init``) is now handled
inline as a startup callback.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import SpecHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps
    from ai.backend.manager.config.provider import ManagerConfigProvider


log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


def register_spec_routes(
    handler: SpecHandler,
    route_deps: RouteDeps,
    *,
    config_provider: ManagerConfigProvider,
) -> RouteRegistry:
    """Build the spec sub-application."""
    from aiohttp import web

    async def _spec_startup(_app: web.Application) -> None:
        """Log a warning when OpenAPI schema introspection is enabled."""
        if config_provider.config.api.allow_openapi_schema_introspection:
            log.warning(
                "OpenAPI schema introspection is enabled. "
                "It is strongly advised to disable this in production setups."
            )

    reg = RouteRegistry.create("spec", route_deps.cors_options)

    # Lifecycle: warn about introspection at startup
    reg.app.on_startup.append(_spec_startup)

    reg.add(
        "GET",
        "/graphiql",
        handler.render_graphiql_graphene_html,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/graphiql/strawberry",
        handler.render_graphiql_strawberry_html,
    )
    reg.add(
        "GET",
        "/openapi",
        handler.render_openapi_html,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/openapi/spec.json",
        handler.generate_openapi_spec,
        middlewares=[auth_required],
    )
    return reg
