"""Spec module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_spec_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the spec sub-application."""
    from ai.backend.manager.api.spec import init as spec_init

    from .handler import SpecHandler

    reg = RouteRegistry.create("spec", deps.cors_options)

    # Wire lifecycle hook -- spec_init reads root context directly,
    # no PrivateContext needed.
    reg.app.on_startup.append(spec_init)

    handler = SpecHandler()

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
