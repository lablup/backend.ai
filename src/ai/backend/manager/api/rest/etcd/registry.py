"""Etcd (config) module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_etcd_module(deps: ModuleDeps) -> RouteRegistry:
    """Build the etcd config sub-application."""
    from ai.backend.manager.api.etcd import app_ctx as etcd_app_ctx

    from .handler import EtcdHandler

    reg = RouteRegistry.create("config", deps.cors_options)

    # Wire lifecycle hook -- etcd_app_ctx reads root context directly,
    # no PrivateContext needed.
    reg.app.cleanup_ctx.append(etcd_app_ctx)

    handler = EtcdHandler()

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
