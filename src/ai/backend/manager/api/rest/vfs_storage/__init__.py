"""New-style VFS storage module using RouteRegistry and constructor DI."""

from __future__ import annotations

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import VFSStorageHandler


def register_routes(
    registry: RouteRegistry,
) -> None:
    """Register VFS storage routes on the given RouteRegistry."""
    handler = VFSStorageHandler()

    registry.add(
        "POST",
        "/vfs-storages/{storage_name}/download",
        handler.download_file,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/vfs-storages/{storage_name}/files",
        handler.list_files,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/vfs-storages/{storage_name}",
        handler.get_storage,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/vfs-storages",
        handler.list_storages,
        middlewares=[auth_required],
    )
