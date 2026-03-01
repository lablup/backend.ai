from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import register_vfolder_module

if TYPE_CHECKING:
    from ai.backend.manager.api.rest.routing import RouteRegistry

__all__ = ["register_vfolder_module"]


def register_routes(registry: RouteRegistry) -> None:
    """Backward-compatible shim -- delegates to the old inline logic.

    The canonical entry-point is :func:`register_vfolder_module`; this wrapper
    exists only so that ``server.py`` keeps working until it is migrated to
    the new ``ModuleDeps`` convention.
    """
    import functools
    import uuid
    from collections.abc import Mapping, Sequence
    from typing import Any

    from aiohttp import web

    from ai.backend.manager.api import ManagerStatus
    from ai.backend.manager.api.manager import ALL_ALLOWED, READ_ALLOWED, server_status_required
    from ai.backend.manager.api.rest.middleware.auth import (
        admin_required,
        auth_required,
        superadmin_required,
    )
    from ai.backend.manager.api.rest.types import RouteMiddleware, WebRequestHandler
    from ai.backend.manager.api.vfolder import (
        check_vfolder_status,
        resolve_vfolder_rows,
    )
    from ai.backend.manager.errors.storage import TooManyVFoldersFound, VFolderNotFound
    from ai.backend.manager.models.vfolder import (
        VFolderPermission,
        VFolderPermissionSetAlias,
        VFolderStatusSet,
    )

    from .handler import VFolderHandler

    def _server_status_required_middleware(
        allowed_status: frozenset[ManagerStatus],
    ) -> RouteMiddleware:
        return server_status_required(allowed_status)

    def _vfolder_resolver(
        perm: VFolderPermissionSetAlias | VFolderPermission,
        status: VFolderStatusSet,
        *,
        allow_privileged_access: bool = False,
    ) -> RouteMiddleware:
        def middleware(handler: WebRequestHandler) -> WebRequestHandler:
            @functools.wraps(handler)
            async def wrapper(request: web.Request) -> web.StreamResponse:
                piece = request.match_info["name"]
                folder_name_or_id: str | uuid.UUID
                try:
                    folder_name_or_id = uuid.UUID(piece)
                except ValueError:
                    folder_name_or_id = piece
                vfolder_rows: Sequence[Mapping[str, Any]] = await resolve_vfolder_rows(
                    request,
                    perm,
                    folder_name_or_id,
                    allow_privileged_access=allow_privileged_access,
                )
                if len(vfolder_rows) > 1:
                    raise TooManyVFoldersFound(vfolder_rows)
                if len(vfolder_rows) == 0:
                    raise VFolderNotFound()
                row = vfolder_rows[0]
                await check_vfolder_status(row, status)
                request["vfolder_row"] = row
                return await handler(request)

            return wrapper

        return middleware

    handler = VFolderHandler()

    def _auth_rw() -> list[RouteMiddleware]:
        return [auth_required, _server_status_required_middleware(ALL_ALLOWED)]

    def _auth_ro() -> list[RouteMiddleware]:
        return [auth_required, _server_status_required_middleware(READ_ALLOWED)]

    def _superadmin_rw() -> list[RouteMiddleware]:
        return [superadmin_required, _server_status_required_middleware(ALL_ALLOWED)]

    def _superadmin_ro() -> list[RouteMiddleware]:
        return [superadmin_required, _server_status_required_middleware(READ_ALLOWED)]

    def _admin_rw() -> list[RouteMiddleware]:
        return [admin_required, _server_status_required_middleware(ALL_ALLOWED)]

    # --- Root resource ---
    registry.add("POST", "", handler.create, middlewares=_auth_rw())
    registry.add("GET", "", handler.list_folders, middlewares=_auth_ro())
    registry.add("DELETE", "", handler.delete_by_id, middlewares=_auth_rw())

    # --- Named resource ---
    registry.add(
        "GET",
        "/{name}",
        handler.get_info,
        middlewares=[
            *_auth_ro(),
            _vfolder_resolver(VFolderPermissionSetAlias.READABLE, VFolderStatusSet.READABLE),
        ],
    )
    registry.add("DELETE", "/{name}", handler.delete_by_name, middlewares=_auth_rw())

    # --- Utility endpoints ---
    registry.add("GET", "/_/id", handler.get_vfolder_id, middlewares=_auth_ro())
    registry.add("GET", "/_/hosts", handler.list_hosts, middlewares=_auth_ro())
    registry.add("GET", "/_/all-hosts", handler.list_all_hosts, middlewares=_superadmin_ro())
    registry.add("GET", "/_/allowed-types", handler.list_allowed_types, middlewares=_auth_ro())
    registry.add("GET", "/_/all_hosts", handler.list_all_hosts, middlewares=_superadmin_ro())
    registry.add("GET", "/_/allowed_types", handler.list_allowed_types, middlewares=_auth_ro())
    registry.add(
        "GET", "/_/perf-metric", handler.get_volume_perf_metric, middlewares=_superadmin_ro()
    )

    # --- VFolder operations (name-based) ---
    registry.add(
        "POST",
        "/{name}/rename",
        handler.rename_vfolder,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermission.OWNER_PERM, VFolderStatusSet.READABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/update-options",
        handler.update_vfolder_options,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermission.OWNER_PERM, VFolderStatusSet.UPDATABLE),
        ],
    )

    # --- File operations ---
    registry.add(
        "POST",
        "/{name}/mkdir",
        handler.mkdir,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/request-upload",
        handler.create_upload_session,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/request-download",
        handler.create_download_session,
        middlewares=[
            *_auth_ro(),
            _vfolder_resolver(VFolderPermissionSetAlias.READABLE, VFolderStatusSet.READABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/request-download-archive",
        handler.create_archive_download_session,
        middlewares=[
            *_auth_ro(),
            _vfolder_resolver(VFolderPermissionSetAlias.READABLE, VFolderStatusSet.READABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/move-file",
        handler.move_file,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/rename-file",
        handler.rename_file,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/delete-files",
        handler.delete_files,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "DELETE",
        "/{name}/delete-files",
        handler.delete_files,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/delete-files-async",
        handler.delete_files_async,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    # Legacy underbar variants
    registry.add(
        "POST",
        "/{name}/rename_file",
        handler.rename_file,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "DELETE",
        "/{name}/delete_files",
        handler.delete_files,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.WRITABLE, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "GET",
        "/{name}/files",
        handler.list_files,
        middlewares=[
            *_auth_ro(),
            _vfolder_resolver(VFolderPermissionSetAlias.READABLE, VFolderStatusSet.READABLE),
        ],
    )

    # --- Invitation endpoints ---
    registry.add(
        "POST",
        "/{name}/invite",
        handler.invite,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermission.OWNER_PERM, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/leave",
        handler.leave,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(
                VFolderPermissionSetAlias.READABLE,
                VFolderStatusSet.UPDATABLE,
                allow_privileged_access=False,
            ),
        ],
    )
    registry.add(
        "POST",
        "/{name}/share",
        handler.share,
        middlewares=[
            *_admin_rw(),
            _vfolder_resolver(VFolderPermission.READ_ONLY, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/unshare",
        handler.unshare,
        middlewares=[
            *_admin_rw(),
            _vfolder_resolver(VFolderPermission.READ_ONLY, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "DELETE",
        "/{name}/unshare",
        handler.unshare,
        middlewares=[
            *_admin_rw(),
            _vfolder_resolver(VFolderPermission.READ_ONLY, VFolderStatusSet.UPDATABLE),
        ],
    )
    registry.add(
        "POST",
        "/{name}/clone",
        handler.clone,
        middlewares=[
            *_auth_rw(),
            _vfolder_resolver(VFolderPermissionSetAlias.READABLE, VFolderStatusSet.UPDATABLE),
        ],
    )

    # --- Trash / purge / restore ---
    registry.add("POST", "/purge", handler.purge, middlewares=_auth_rw())
    registry.add("POST", "/restore-from-trash-bin", handler.restore, middlewares=_auth_rw())
    registry.add(
        "POST",
        "/delete-from-trash-bin",
        handler.delete_from_trash_bin,
        middlewares=_auth_rw(),
    )
    registry.add("DELETE", "/{folder_id}/force", handler.force_delete, middlewares=_auth_rw())

    # --- Invitation management ---
    registry.add(
        "GET", "/invitations/list-sent", handler.list_sent_invitations, middlewares=_auth_ro()
    )
    registry.add(
        "GET",
        "/invitations/list_sent",
        handler.list_sent_invitations,
        middlewares=_auth_ro(),
    )
    registry.add(
        "POST", "/invitations/update/{inv_id}", handler.update_invitation, middlewares=_auth_rw()
    )
    registry.add("GET", "/invitations/list", handler.invitations, middlewares=_auth_ro())
    registry.add("POST", "/invitations/accept", handler.accept_invitation, middlewares=_auth_rw())
    registry.add("POST", "/invitations/delete", handler.delete_invitation, middlewares=_auth_rw())
    registry.add("DELETE", "/invitations/delete", handler.delete_invitation, middlewares=_auth_rw())

    # --- Shared vfolders ---
    registry.add("GET", "/_/shared", handler.list_shared_vfolders, middlewares=_auth_ro())
    registry.add("POST", "/_/shared", handler.update_shared_vfolder, middlewares=_auth_rw())
    registry.add(
        "POST", "/_/sharing", handler.update_vfolder_sharing_status, middlewares=_auth_rw()
    )

    # --- Admin: fstab, mounts, quota, usage ---
    registry.add("GET", "/_/fstab", handler.get_fstab_contents, middlewares=_superadmin_ro())
    registry.add("GET", "/_/mounts", handler.list_mounts, middlewares=_superadmin_ro())
    registry.add("POST", "/_/mounts", handler.mount_host, middlewares=_superadmin_rw())
    registry.add("POST", "/_/umounts", handler.umount_host, middlewares=_superadmin_rw())
    registry.add("DELETE", "/_/mounts", handler.umount_host, middlewares=_superadmin_rw())
    registry.add(
        "POST",
        "/_/change-ownership",
        handler.change_vfolder_ownership,
        middlewares=_superadmin_rw(),
    )
    registry.add("GET", "/_/quota", handler.get_quota, middlewares=_auth_ro())
    registry.add("POST", "/_/quota", handler.update_quota, middlewares=_auth_rw())
    registry.add("GET", "/_/usage", handler.get_usage, middlewares=_superadmin_ro())
    registry.add("GET", "/_/used-bytes", handler.get_used_bytes, middlewares=_superadmin_ro())
