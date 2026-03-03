"""Spec module registrar.

The lifecycle hook (previously in ``api.spec.init``) is now handled
inline as a startup callback.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext
    from ai.backend.manager.api.rest.types import ModuleDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def _spec_startup(app: web.Application) -> None:
    """Log a warning when OpenAPI schema introspection is enabled."""
    root_ctx: RootContext = app["_root.context"]
    if root_ctx.config_provider.config.api.allow_openapi_schema_introspection:
        log.warning(
            "OpenAPI schema introspection is enabled. "
            "It is strongly advised to disable this in production setups."
        )


def register_spec_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the spec sub-application."""
    from .handler import SpecHandler

    reg = RouteRegistry.create("spec", deps.cors_options)

    # Lifecycle: warn about introspection at startup
    reg.app.on_startup.append(_spec_startup)

    handler = SpecHandler(config_provider=deps.config_provider)

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
