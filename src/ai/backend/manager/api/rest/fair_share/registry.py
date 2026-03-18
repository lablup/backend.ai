"""Fair share module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import FairShareAPIHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_fair_share_routes(
    handler: FairShareAPIHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the fair share sub-application."""

    reg = RouteRegistry.create("fair-share", route_deps.cors_options)

    # Domain fair share routes (superadmin)
    reg.add(
        "GET",
        "/domains/{resource_group}/{domain_name}",
        handler.get_domain_fair_share,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/domains/search",
        handler.search_domain_fair_shares,
        middlewares=[superadmin_required],
    )

    # Project fair share routes (superadmin)
    reg.add(
        "GET",
        "/projects/{resource_group}/{project_id}",
        handler.get_project_fair_share,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/projects/search",
        handler.search_project_fair_shares,
        middlewares=[superadmin_required],
    )

    # User fair share routes (superadmin)
    reg.add(
        "GET",
        "/users/{resource_group}/{project_id}/{user_uuid}",
        handler.get_user_fair_share,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/users/search",
        handler.search_user_fair_shares,
        middlewares=[superadmin_required],
    )

    # Usage bucket routes (superadmin)
    reg.add(
        "POST",
        "/usage-buckets/domains/search",
        handler.search_domain_usage_buckets,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/usage-buckets/projects/search",
        handler.search_project_usage_buckets,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/usage-buckets/users/search",
        handler.search_user_usage_buckets,
        middlewares=[superadmin_required],
    )

    # RG-scoped usage bucket routes (auth required)
    reg.add(
        "POST",
        "/rg/{resource_group}/usage-buckets/domains/search",
        handler.rg_search_domain_usage_buckets,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/rg/{resource_group}/domains/{domain_name}/usage-buckets/projects/search",
        handler.rg_search_project_usage_buckets,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/rg/{resource_group}/domains/{domain_name}/projects/{project_id}/usage-buckets/users/search",
        handler.rg_search_user_usage_buckets,
        middlewares=[auth_required],
    )

    # RG-scoped domain fair share routes (auth required)
    reg.add(
        "GET",
        "/rg/{resource_group}/domains/{domain_name}",
        handler.rg_get_domain_fair_share,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/rg/{resource_group}/domains/search",
        handler.rg_search_domain_fair_shares,
        middlewares=[auth_required],
    )

    # RG-scoped project fair share routes (auth required)
    reg.add(
        "GET",
        "/rg/{resource_group}/domains/{domain_name}/projects/{project_id}",
        handler.rg_get_project_fair_share,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/rg/{resource_group}/domains/{domain_name}/projects/search",
        handler.rg_search_project_fair_shares,
        middlewares=[auth_required],
    )

    # RG-scoped user fair share routes (auth required)
    reg.add(
        "GET",
        "/rg/{resource_group}/domains/{domain_name}/projects/{project_id}/users/{user_uuid}",
        handler.rg_get_user_fair_share,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/rg/{resource_group}/domains/{domain_name}/projects/{project_id}/users/search",
        handler.rg_search_user_fair_shares,
        middlewares=[auth_required],
    )

    # Upsert weight routes (superadmin)
    reg.add(
        "PUT",
        "/domains/{resource_group}/{domain_name}/weight",
        handler.upsert_domain_fair_share_weight,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PUT",
        "/projects/{resource_group}/{project_id}/weight",
        handler.upsert_project_fair_share_weight,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PUT",
        "/users/{resource_group}/{project_id}/{user_uuid}/weight",
        handler.upsert_user_fair_share_weight,
        middlewares=[superadmin_required],
    )

    # Bulk upsert weight routes (superadmin)
    reg.add(
        "POST",
        "/domains/bulk-upsert-weight",
        handler.bulk_upsert_domain_fair_share_weight,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/projects/bulk-upsert-weight",
        handler.bulk_upsert_project_fair_share_weight,
        middlewares=[superadmin_required],
    )
    reg.add(
        "POST",
        "/users/bulk-upsert-weight",
        handler.bulk_upsert_user_fair_share_weight,
        middlewares=[superadmin_required],
    )

    # Resource group spec routes (superadmin)
    reg.add(
        "GET",
        "/resource-groups/{resource_group}/spec",
        handler.get_resource_group_fair_share_spec,
        middlewares=[superadmin_required],
    )
    reg.add(
        "GET",
        "/resource-groups/specs",
        handler.search_resource_group_fair_share_specs,
        middlewares=[superadmin_required],
    )
    reg.add(
        "PATCH",
        "/resource-groups/{resource_group}/spec",
        handler.update_resource_group_fair_share_spec,
        middlewares=[superadmin_required],
    )
    return reg
