"""VFS storage module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import ModuleDeps


def register_vfs_storage_routes(deps: ModuleDeps) -> RouteRegistry:
    """Build the VFS storage sub-application."""
    # Import handler inside function to avoid circular imports
    from .handler import VFSStorageHandler

    reg = RouteRegistry.create("vfs-storages", deps.cors_options)
    reg.app["_storage_manager"] = deps.storage_manager
    handler = VFSStorageHandler()

    reg.add(
        "POST",
        "/{storage_name}/download",
        handler.download_file,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/{storage_name}/files",
        handler.list_files,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/{storage_name}",
        handler.get_storage,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/",
        handler.list_storages,
        middlewares=[auth_required],
    )
    return reg
