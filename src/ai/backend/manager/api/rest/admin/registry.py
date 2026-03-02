"""Admin tree-builder registrar.

Assembles the admin module's own routes (GraphQL endpoints) together with
six sub-registries: domains, users, images, rbac, quota-scopes, and
auto-scaling-rules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.admin import PrivateContext as AdminPrivateContext
from ai.backend.manager.api.admin import init as admin_init
from ai.backend.manager.api.admin import shutdown as admin_shutdown
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
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_admin_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the admin tree: admin's own routes + six sub-registries."""
    reg = RouteRegistry.create("admin", deps.cors_options)

    # Admin private context + lifecycle hooks
    ctx = AdminPrivateContext()
    reg.app["admin.context"] = ctx
    reg.app.on_startup.append(admin_init)
    reg.app.on_shutdown.append(admin_shutdown)

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
