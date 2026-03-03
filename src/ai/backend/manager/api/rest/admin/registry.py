"""Admin tree-builder registrar.

Assembles the admin module's own routes (GraphQL endpoints) together with
six sub-registries: domains, users, images, rbac, quota-scopes, and
auto-scaling-rules.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql_legacy.schema import graphene_schema
from ai.backend.manager.api.rest.auto_scaling_rule.registry import register_auto_scaling_rule_routes
from ai.backend.manager.api.rest.domain.registry import register_domain_routes
from ai.backend.manager.api.rest.image.registry import register_image_routes
from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.quota_scope.registry import register_quota_scope_routes
from ai.backend.manager.api.rest.rbac.registry import register_rbac_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.user.registry import register_user_routes

from .handler import AdminHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext
    from ai.backend.manager.api.rest.types import ModuleDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def _admin_startup(app: web.Application) -> None:
    """Log a warning when GraphQL schema introspection is enabled."""
    root_ctx: RootContext = app["_root.context"]
    if root_ctx.config_provider.config.api.allow_graphql_schema_introspection:
        log.warning(
            "GraphQL schema introspection is enabled. "
            "It is strongly advised to disable this in production setups."
        )


def register_admin_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the admin tree: admin's own routes + six sub-registries."""
    reg = RouteRegistry.create("admin", deps.cors_options)

    # Lifecycle: warn about introspection at startup
    reg.app.on_startup.append(_admin_startup)

    # Admin's own routes (GraphQL)
    if deps.gql_context_deps is None:
        raise RuntimeError("GQLContextDeps required for admin routes")
    handler = AdminHandler(gql_schema=graphene_schema, gql_deps=deps.gql_context_deps)
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

    # Sub-registries
    reg.add_subregistry(register_domain_routes(deps))
    reg.add_subregistry(register_user_routes(deps))
    reg.add_subregistry(register_image_routes(deps))
    reg.add_subregistry(register_rbac_routes(deps))
    reg.add_subregistry(register_quota_scope_routes(deps))
    reg.add_subregistry(register_auto_scaling_rule_routes(deps))

    return reg
