from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_etcd_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry

__all__ = ["register_etcd_module"]


def register_routes(registry: RouteRegistry) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_etcd_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required

    from .handler import EtcdHandler

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
