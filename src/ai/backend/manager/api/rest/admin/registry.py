"""Admin tree-builder registrar.

Assembles the admin module's own routes (GraphQL endpoints) together with
pre-built sub-registries passed by the composition root.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import AdminHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_admin_routes(
    handler: AdminHandler,
    route_deps: RouteDeps,
    sub_registries: Sequence[RouteRegistry],
) -> RouteRegistry:
    """Build the admin tree: admin's own routes + pre-built sub-registries."""
    reg = RouteRegistry.create("admin", route_deps.cors_options)

    reg.add(
        "POST",
        "/graphql",
        handler.handle_gql_legacy,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/gql",
        handler.handle_gql_graphene,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/gql/v2",
        handler.handle_gql_strawberry,
        middlewares=[auth_required],
    )

    # Sub-registries (built by the composition root)
    for sub in sub_registries:
        reg.add_subregistry(sub)

    return reg
