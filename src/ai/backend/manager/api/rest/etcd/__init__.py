"""New-style etcd (config) module using RouteRegistry."""

from __future__ import annotations

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import EtcdHandler


def register_routes(registry: RouteRegistry) -> None:
    """Register etcd config routes on the given RouteRegistry."""
    handler = EtcdHandler()

    # Public endpoints (auth_required only)
    registry.add("GET", "/resource-slots", handler.get_resource_slots, middlewares=[auth_required])
    registry.add(
        "GET",
        "/resource-slots/details",
        handler.get_resource_metadata,
        middlewares=[auth_required],
    )
    registry.add("GET", "/vfolder-types", handler.get_vfolder_types, middlewares=[auth_required])

    # Deprecated endpoint
    registry.add(
        "GET",
        "/docker-registries",
        handler.get_docker_registries,
        middlewares=[superadmin_required],
    )

    # Superadmin raw etcd access
    registry.add("POST", "/get", handler.get_config, middlewares=[superadmin_required])
    registry.add("POST", "/set", handler.set_config, middlewares=[superadmin_required])
    registry.add("POST", "/delete", handler.delete_config, middlewares=[superadmin_required])
