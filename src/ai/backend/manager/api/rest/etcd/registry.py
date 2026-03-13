"""Etcd (config) module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import EtcdHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps
    from ai.backend.manager.config.provider import ManagerConfigProvider


def register_etcd_routes(
    handler: EtcdHandler,
    route_deps: RouteDeps,
    *,
    pidx: int,
    config_provider: ManagerConfigProvider,
) -> RouteRegistry:
    """Build the etcd config sub-application."""
    from .lifecycle import make_app_ctx

    reg = RouteRegistry.create("config", route_deps.cors_options)

    # Wire lifecycle hook via factory closure
    reg.app.cleanup_ctx.append(make_app_ctx(pidx, config_provider))

    # Public endpoints (auth_required only)
    reg.add("GET", "/resource-slots", handler.get_resource_slots, middlewares=[auth_required])
    reg.add(
        "GET",
        "/resource-slots/details",
        handler.get_resource_metadata,
        middlewares=[auth_required],
    )
    reg.add("GET", "/vfolder-types", handler.get_vfolder_types, middlewares=[auth_required])

    # Deprecated endpoint
    reg.add(
        "GET",
        "/docker-registries",
        handler.get_docker_registries,
        middlewares=[superadmin_required],
    )

    # Superadmin raw etcd access
    reg.add("POST", "/get", handler.get_config, middlewares=[superadmin_required])
    reg.add("POST", "/set", handler.set_config, middlewares=[superadmin_required])
    reg.add("POST", "/delete", handler.delete_config, middlewares=[superadmin_required])
    return reg
