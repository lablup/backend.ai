"""Route registry for v2 VFolder endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import auth_required, superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps

    from .handler import V2VFolderHandler


def register_v2_vfolder_routes(
    handler: V2VFolderHandler,
    route_deps: RouteDeps,
) -> RouteRegistry:
    """Build and return the route registry for VFolder endpoints."""
    registry = RouteRegistry.create("vfolders", route_deps.cors_options)

    registry.add(
        "POST",
        "/my/search",
        handler.my_search,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/projects/{project_id}/search",
        handler.project_search,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "",
        handler.create,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{vfolder_id}/upload-session",
        handler.create_upload_session,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/search",
        handler.admin_search,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/{vfolder_id}",
        handler.get,
        middlewares=[auth_required],
    )
    registry.add(
        "DELETE",
        "/{vfolder_id}",
        handler.delete,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{vfolder_id}/purge",
        handler.purge,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{vfolder_id}/files/list",
        handler.list_files,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{vfolder_id}/files/mkdir",
        handler.mkdir,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{vfolder_id}/files/move",
        handler.move_file,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{vfolder_id}/files/delete",
        handler.delete_files,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{vfolder_id}/download-session",
        handler.create_download_session,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/{vfolder_id}/clone",
        handler.clone,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/delete",
        handler.bulk_delete,
        middlewares=[auth_required],
    )
    registry.add(
        "POST",
        "/purge",
        handler.bulk_purge,
        middlewares=[auth_required],
    )

    return registry
