"""VFolder module registrar."""

from __future__ import annotations

import functools
import uuid
from typing import TYPE_CHECKING

from aiohttp import web

from ai.backend.manager.api.rest.middleware.auth import (
    admin_required,
    auth_required,
    superadmin_required,
)
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteMiddleware, WebRequestHandler
from ai.backend.manager.models.vfolder import (
    VFolderPermission,
    VFolderPermissionSetAlias,
    VFolderStatusSet,
)
from ai.backend.manager.services.vfolder.actions.base import GetAccessibleVFolderAction

from .handler import VFolderHandler

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.types import RouteDeps
    from ai.backend.manager.services.processors import Processors


def _vfolder_resolver(
    perm: VFolderPermissionSetAlias | VFolderPermission,
    status: VFolderStatusSet,
    *,
    processors: Processors,
    allow_privileged_access: bool = False,
) -> RouteMiddleware:
    """Route middleware that resolves vfolder rows and checks status.

    Uses the ``get_accessible_vfolder`` processor to resolve, validate
    count (0 → NotFound, >1 → TooMany), and check status in a single call.

    Sets ``request["vfolder_row"]`` so that ``VFolderAuthContext`` can
    extract the row in handler methods.
    """

    def middleware(handler: WebRequestHandler) -> WebRequestHandler:
        @functools.wraps(handler)
        async def wrapper(request: web.Request) -> web.StreamResponse:
            piece = request.match_info["name"]
            folder_name_or_id: str | uuid.UUID
            try:
                folder_name_or_id = uuid.UUID(piece)
            except ValueError:
                folder_name_or_id = piece
            result = await processors.vfolder.get_accessible_vfolder.wait_for_complete(
                GetAccessibleVFolderAction(
                    user_uuid=request["user"]["uuid"],
                    user_role=request["user"]["role"],
                    domain_name=request["user"]["domain_name"],
                    is_admin=request["is_admin"],
                    perm=perm,
                    folder_id_or_name=folder_name_or_id,
                    required_status=status,
                    allow_privileged_access=allow_privileged_access,
                )
            )
            request["vfolder_row"] = result.row
            return await handler(request)

        return wrapper

    return middleware


def register_vfolder_routes(
    handler: VFolderHandler,
    route_deps: RouteDeps,
    *,
    processors: Processors,
) -> RouteRegistry:
    """Build the vfolder sub-application."""
    from .lifecycle import PrivateContext as VfolderPrivateContext
    from .lifecycle import init as vfolder_init
    from .lifecycle import shutdown as vfolder_shutdown

    reg = RouteRegistry.create("folders", route_deps.cors_options)
    ctx = VfolderPrivateContext()

    # Store ctx on app dict for backward compatibility (lifecycle functions
    # read from app["folders.context"]).
    reg.app["folders.context"] = ctx

    # Wire lifecycle hooks
    reg.app.on_startup.append(vfolder_init)
    reg.app.on_shutdown.append(vfolder_shutdown)

    # Helper to build middleware lists
    def _auth_rw() -> list[RouteMiddleware]:
        return [auth_required, route_deps.all_status_mw]

    def _auth_ro() -> list[RouteMiddleware]:
        return [auth_required, route_deps.read_status_mw]

    def _superadmin_rw() -> list[RouteMiddleware]:
        return [superadmin_required, route_deps.all_status_mw]

    def _superadmin_ro() -> list[RouteMiddleware]:
        return [superadmin_required, route_deps.read_status_mw]

    def _admin_rw() -> list[RouteMiddleware]:
        return [admin_required, route_deps.all_status_mw]

    # --- Root resource: POST / (create), GET / (list), DELETE / (delete_by_id) ---
    reg.add("POST", "", handler.create, middlewares=_auth_rw())
    reg.add("GET", "", handler.list_folders, middlewares=_auth_ro())
    reg.add("DELETE", "", handler.delete_by_id, middlewares=_auth_rw())

    # --- Named resource: GET /{name} (get_info), DELETE /{name} (delete_by_name) ---
    reg.add(
        "GET",
        "/{name}",
        handler.get_info,
        middlewares=[
            *_auth_ro(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.READABLE,
                VFolderStatusSet.READABLE,
                processors=processors,
            ),
        ],
    )
    reg.add("DELETE", "/{name}", handler.delete_by_name, middlewares=_auth_rw())

    # --- Utility endpoints ---
    reg.add("GET", "/_/id", handler.get_vfolder_id, middlewares=_auth_ro())
    reg.add("GET", "/_/hosts", handler.list_hosts, middlewares=_auth_ro())
    reg.add("GET", "/_/all-hosts", handler.list_all_hosts, middlewares=_superadmin_ro())
    reg.add("GET", "/_/allowed-types", handler.list_allowed_types, middlewares=_auth_ro())
    reg.add(
        "GET", "/_/all_hosts", handler.list_all_hosts, middlewares=_superadmin_ro()
    )  # legacy underbar
    reg.add(
        "GET", "/_/allowed_types", handler.list_allowed_types, middlewares=_auth_ro()
    )  # legacy underbar
    reg.add("GET", "/_/perf-metric", handler.get_volume_perf_metric, middlewares=_superadmin_ro())

    # --- VFolder operations (name-based) ---
    reg.add(
        "POST",
        "/{name}/rename",
        handler.rename_vfolder,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermission.OWNER_PERM, VFolderStatusSet.READABLE, processors=processors
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/update-options",
        handler.update_vfolder_options,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermission.OWNER_PERM, VFolderStatusSet.UPDATABLE, processors=processors
            ),
        ],
    )

    # --- File operations ---
    reg.add(
        "POST",
        "/{name}/mkdir",
        handler.mkdir,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/request-upload",
        handler.create_upload_session,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/request-download",
        handler.create_download_session,
        middlewares=[
            *_auth_ro(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.READABLE,
                VFolderStatusSet.READABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/request-download-archive",
        handler.create_archive_download_session,
        middlewares=[
            *_auth_ro(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.READABLE,
                VFolderStatusSet.READABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/move-file",
        handler.move_file,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/rename-file",
        handler.rename_file,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/delete-files",
        handler.delete_files,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "DELETE",
        "/{name}/delete-files",
        handler.delete_files,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/delete-files-async",
        handler.delete_files_async,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    # Legacy underbar variants
    reg.add(
        "POST",
        "/{name}/rename_file",
        handler.rename_file,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "DELETE",
        "/{name}/delete_files",
        handler.delete_files,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.WRITABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )
    reg.add(
        "GET",
        "/{name}/files",
        handler.list_files,
        middlewares=[
            *_auth_ro(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.READABLE,
                VFolderStatusSet.READABLE,
                processors=processors,
            ),
        ],
    )

    # --- Invitation endpoints ---
    reg.add(
        "POST",
        "/{name}/invite",
        handler.invite,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermission.OWNER_PERM, VFolderStatusSet.UPDATABLE, processors=processors
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/leave",
        handler.leave,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.READABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
                allow_privileged_access=False,
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/share",
        handler.share,
        middlewares=[
            *_admin_rw(),
            _vfolder_resolver(
                VFolderPermission.READ_ONLY, VFolderStatusSet.UPDATABLE, processors=processors
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/unshare",
        handler.unshare,
        middlewares=[
            *_admin_rw(),
            _vfolder_resolver(
                VFolderPermission.READ_ONLY, VFolderStatusSet.UPDATABLE, processors=processors
            ),
        ],
    )
    reg.add(
        "DELETE",
        "/{name}/unshare",
        handler.unshare,
        middlewares=[
            *_admin_rw(),
            _vfolder_resolver(
                VFolderPermission.READ_ONLY, VFolderStatusSet.UPDATABLE, processors=processors
            ),
        ],
    )
    reg.add(
        "POST",
        "/{name}/clone",
        handler.clone,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.READABLE,
                VFolderStatusSet.UPDATABLE,
                processors=processors,
            ),
        ],
    )

    # --- Trash / purge / restore ---
    reg.add("POST", "/purge", handler.purge, middlewares=_auth_rw())
    reg.add("POST", "/restore-from-trash-bin", handler.restore, middlewares=_auth_rw())
    reg.add(
        "POST",
        "/delete-from-trash-bin",
        handler.delete_from_trash_bin,
        middlewares=_auth_rw(),
    )
    reg.add("DELETE", "/{folder_id}/force", handler.force_delete, middlewares=_auth_rw())

    # --- Invitation management ---
    reg.add("GET", "/invitations/list-sent", handler.list_sent_invitations, middlewares=_auth_ro())
    reg.add(
        "GET",
        "/invitations/list_sent",
        handler.list_sent_invitations,
        middlewares=_auth_ro(),
    )  # legacy underbar
    reg.add(
        "POST", "/invitations/update/{inv_id}", handler.update_invitation, middlewares=_auth_rw()
    )
    reg.add("GET", "/invitations/list", handler.invitations, middlewares=_auth_ro())
    reg.add("POST", "/invitations/accept", handler.accept_invitation, middlewares=_auth_rw())
    reg.add("POST", "/invitations/delete", handler.delete_invitation, middlewares=_auth_rw())
    reg.add("DELETE", "/invitations/delete", handler.delete_invitation, middlewares=_auth_rw())

    # --- Shared vfolders ---
    reg.add("GET", "/_/shared", handler.list_shared_vfolders, middlewares=_auth_ro())
    reg.add("POST", "/_/shared", handler.update_shared_vfolder, middlewares=_auth_rw())
    reg.add("POST", "/_/sharing", handler.update_vfolder_sharing_status, middlewares=_auth_rw())

    # --- Admin: fstab, mounts, quota, usage ---
    reg.add("GET", "/_/fstab", handler.get_fstab_contents, middlewares=_superadmin_ro())
    reg.add("GET", "/_/mounts", handler.list_mounts, middlewares=_superadmin_ro())
    reg.add("POST", "/_/mounts", handler.mount_host, middlewares=_superadmin_rw())
    reg.add("POST", "/_/umounts", handler.umount_host, middlewares=_superadmin_rw())
    reg.add("DELETE", "/_/mounts", handler.umount_host, middlewares=_superadmin_rw())
    reg.add(
        "POST",
        "/_/change-ownership",
        handler.change_vfolder_ownership,
        middlewares=_superadmin_rw(),
    )
    reg.add("GET", "/_/quota", handler.get_quota, middlewares=_auth_ro())
    reg.add("POST", "/_/quota", handler.update_quota, middlewares=_auth_rw())
    reg.add("GET", "/_/usage", handler.get_usage, middlewares=_superadmin_ro())
    reg.add("GET", "/_/used-bytes", handler.get_used_bytes, middlewares=_superadmin_ro())
    return reg
