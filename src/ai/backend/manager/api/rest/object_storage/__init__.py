"""New-style object storage module using RouteRegistry and constructor DI."""

from __future__ import annotations

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ObjectStorageHandler


def register_routes(
    registry: RouteRegistry,
) -> None:
    """Register object storage routes on the given RouteRegistry."""
    handler = ObjectStorageHandler()

    registry.add(
        "POST",
        "/presigned/upload",
        handler.get_presigned_upload_url,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/presigned/download",
        handler.get_presigned_download_url,
        middlewares=[auth_required],
    )
    # TODO: deprecate these APIs, and use /storage-namespaces instead
    registry.add(
        "GET",
        "/buckets",
        handler.get_all_buckets,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/{storage_id}/buckets",
        handler.get_buckets,
        middlewares=[auth_required],
    )
    registry.add(
        "GET",
        "/",
        handler.list_object_storages,
        middlewares=[auth_required],
    )
