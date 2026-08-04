from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ConfidentialHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_confidential_shim_routes(
    handler: ConfidentialHandler, route_deps: RouteDeps
) -> RouteRegistry:
    reg = RouteRegistry.create("confidential-shim", route_deps.cors_options)
    reg.add("POST", "/{scaling_group}/kbs/v0/auth", handler.relay_auth)
    reg.add("POST", "/{scaling_group}/kbs/v0/attest", handler.relay_attest)
    reg.add(
        "GET",
        "/{scaling_group}/kbs/v0/resource/{resource_path:.+}",
        handler.relay_resource,
    )
    return reg


def register_confidential_routes(
    handler: ConfidentialHandler, route_deps: RouteDeps
) -> RouteRegistry:
    reg = RouteRegistry.create("confidential", route_deps.cors_options)
    admin = [superadmin_required, route_deps.all_status_mw]
    reg.add("POST", "/scaling-groups/capability", handler.set_capability, middlewares=admin)
    reg.add("POST", "/reference-values", handler.register_reference_value, middlewares=admin)
    reg.add("POST", "/reference-values/drain", handler.drain_reference_value, middlewares=admin)
    reg.add("POST", "/measured-blobs", handler.publish_blob, middlewares=admin)
    reg.add("POST", "/tcb-grace", handler.open_grace, middlewares=admin)
    reg.add("POST", "/decisions/search", handler.list_decisions, middlewares=admin)
    reg.add(
        "POST",
        "/folder-keys",
        handler.release_folder_key,
        middlewares=[auth_required, route_deps.read_status_mw],
    )
    return reg
