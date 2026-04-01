"""Object storage module registrar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import ObjectStorageHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps


def register_object_storage_routes(
    handler: ObjectStorageHandler, route_deps: RouteDeps
) -> RouteRegistry:
    """Build the object storage sub-application."""

    reg = RouteRegistry.create("object-storages", route_deps.cors_options)

    reg.add(
        "POST",
        "/presigned/upload",
        handler.get_presigned_upload_url,
        middlewares=[auth_required],
    )
    reg.add(
        "POST",
        "/presigned/download",
        handler.get_presigned_download_url,
        middlewares=[auth_required],
    )
    # TODO: deprecate these APIs, and use /storage-namespaces instead
    reg.add(
        "GET",
        "/buckets",
        handler.get_all_buckets,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/{storage_id}/buckets",
        handler.get_buckets,
        middlewares=[auth_required],
    )
    reg.add(
        "GET",
        "/",
        handler.list_object_storages,
        middlewares=[auth_required],
    )
    return reg
