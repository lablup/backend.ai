"""Route registry for REST v2 deployment endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import V2DeploymentHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_v2_deployment_routes(
    handler: V2DeploymentHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Register all REST v2 deployment routes and return the sub-registry."""
    registry = RouteRegistry.create("deployments", route_deps.cors_options)

    # ------------------------------------------------------------------
    # Core deployment CRUD
    # ------------------------------------------------------------------
    registry.add(
        "POST",
        "/",
        handler.create,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/search",
        handler.admin_search,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{deployment_id}",
        handler.get,
        middlewares=[auth_required],
    )
    registry.add(
        "PUT",
        "/{deployment_id}",
        handler.update,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/delete",
        handler.delete,
        middlewares=[auth_required],
    )

    # ------------------------------------------------------------------
    # Revision operations
    # ------------------------------------------------------------------
    registry.add(
        "GET",
        "/{deployment_id}/current-revision",
        handler.get_current_revision,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{deployment_id}/revisions",
        handler.add_revision,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/revisions/{revision_id}",
        handler.get_revision,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{deployment_id}/revisions/search",
        handler.search_revisions,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/revisions/search",
        handler.admin_search_revisions,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/{deployment_id}/revisions/activate",
        handler.activate_revision,
        middlewares=[auth_required],
    )

    # ------------------------------------------------------------------
    # Replica operations
    # ------------------------------------------------------------------
    registry.add(
        "POST",
        "/{deployment_id}/replicas/search",
        handler.search_replicas,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/replicas/search",
        handler.admin_search_replicas,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/replicas/{replica_id}",
        handler.get_replica,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{deployment_id}/replicas/sync",
        handler.sync_replicas,
        middlewares=[auth_required],
    )

    # ------------------------------------------------------------------
    # Route operations
    # ------------------------------------------------------------------
    registry.add(
        "POST",
        "/{deployment_id}/routes/search",
        handler.search_routes,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/routes/update-traffic",
        handler.update_route_traffic,
        middlewares=[auth_required],
    )

    # ------------------------------------------------------------------
    # Access token operations
    # ------------------------------------------------------------------
    registry.add(
        "POST",
        "/{deployment_id}/access-tokens",
        handler.create_access_token,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{deployment_id}/access-tokens/search",
        handler.search_access_tokens,
        middlewares=[auth_required],
    )

    # ------------------------------------------------------------------
    # Auto-scaling rule operations
    # ------------------------------------------------------------------
    registry.add(
        "POST",
        "/auto-scaling-rules",
        handler.create_auto_scaling_rule,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{deployment_id}/auto-scaling-rules/search",
        handler.search_auto_scaling_rules,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/auto-scaling-rules/{rule_id}",
        handler.get_auto_scaling_rule,
        middlewares=[auth_required],
    )
    registry.add(
        "PUT",
        "/auto-scaling-rules/{rule_id}",
        handler.update_auto_scaling_rule,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/auto-scaling-rules/delete",
        handler.delete_auto_scaling_rule,
        middlewares=[auth_required],
    )

    # ------------------------------------------------------------------
    # Deployment policy operations
    # ------------------------------------------------------------------
    registry.add(
        "GET",
        "/policies/{deployment_id}",
        handler.get_deployment_policy,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/policies/search",
        handler.search_deployment_policies,
        middlewares=[superadmin_required],
    )
    registry.add(
        "POST",
        "/policies/upsert",
        handler.upsert_deployment_policy,
        middlewares=[superadmin_required],
    )

    return registry
