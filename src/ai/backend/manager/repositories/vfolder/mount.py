from __future__ import annotations

import logging
import os.path
import uuid
from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common.types import (
    MountPermission,
    VFolderHostPermission,
    VFolderID,
    VFolderMount,
    VFolderMountOptions,
    VFolderMountRequest,
    VFolderUsageMode,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.group.types import ProjectType as DataProjectType
from ai.backend.manager.data.vfolder.types import VFolderMountPermission as VFolderPermission
from ai.backend.manager.defs import VFOLDER_DSTPATHS_MAP
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import (
    InsufficientStoragePermission,
    VFolderNotFound,
    VFolderOperationFailed,
    VFolderPermissionError,
)
from ai.backend.manager.models.group import groups as groups_table
from ai.backend.manager.models.vfolder.row import (
    DEAD_VFOLDER_STATUSES,
    VFolderRow,
    check_overlapping_mounts,
    ensure_host_permission_allowed,
    is_mount_duplicate,
    query_accessible_vfolders,
    vfolders,
)
from ai.backend.manager.types import UserScope

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__: Sequence[str] = ("prepare_vfolder_mounts",)


def _normalize_mount_subpath(raw_subpath: str | None) -> str:
    """Normalize a UUID-keyed mount's ``subpath`` option and reject any
    attempt to escape the vfolder root.

    Returns the normalized subpath (or ``"."`` when nothing was supplied).
    Raises :class:`InvalidAPIParameters` when the normalized form would
    leave the vfolder root via ``..``, ``../…``, or an absolute path.

    Note: ``PurePosixPath('..').is_relative_to('.')`` is ``True`` in
    Python ≥ 3.12, so the ``is_relative_to`` shorthand cannot be used
    as the escape guard — the explicit checks below are required.
    """
    candidate = raw_subpath if raw_subpath else "."
    normed = os.path.normpath(candidate)
    if normed == ".." or normed.startswith("../") or PurePosixPath(normed).is_absolute():
        raise InvalidAPIParameters(
            f"The subpath '{candidate}' must not escape the vfolder root.",
        )
    return normed


async def prepare_vfolder_mounts(
    conn: SAConnection,
    storage_manager: StorageSessionManager,
    allowed_vfolder_types: Sequence[str],
    user_scope: UserScope,
    resource_policy: Mapping[str, Any],
    mount_requests: Sequence[VFolderMountRequest],
) -> Sequence[VFolderMount]:
    """
    Determine the actual mount information from the requested vfolder lists,
    vfolder configurations, and the given user scope.
    """
    requested_mounts: list[str] = []
    requested_vfolder_names: dict[str | uuid.UUID | int, str] = {}
    requested_vfolder_ids: set[uuid.UUID] = set()
    requested_vfolder_subpaths: dict[str | uuid.UUID | int, str] = {}
    requested_vfolder_dstpaths: dict[str | uuid.UUID | int, str] = {}
    requested_mount_options: dict[str | uuid.UUID | int, VFolderMountOptions] = {}
    matched_vfolder_mounts: list[VFolderMount] = []
    _already_resolved: set[str] = set()
    # A vfolder referenced by UUID may be requested several times, each with a
    # different subpath/destination. Key each such request by its index in
    # ``mount_requests`` instead of the bare UUID so the entries no longer
    # collapse to one-per-vfolder; ``uuid_request_indices`` records which
    # request keys target each vfolder UUID (lablup/backend.ai#11936).
    uuid_request_indices: dict[uuid.UUID, list[int]] = {}

    # Split the requests into the UUID-referenced and name-referenced surfaces,
    # capturing each request's subpath, destination, and options up front.
    for index, req in enumerate(mount_requests):
        if isinstance(req.ref, uuid.UUID):
            requested_vfolder_ids.add(req.ref)
            uuid_request_indices.setdefault(req.ref, []).append(index)
            requested_mount_options[index] = req.options
            requested_vfolder_subpaths[index] = _normalize_mount_subpath(req.options.subpath)
            if req.dst_path is not None:
                requested_vfolder_dstpaths[index] = req.dst_path
        else:
            name, _, subpath = req.ref.partition("/")
            if not PurePosixPath(os.path.normpath(req.ref)).is_relative_to(name):
                raise InvalidAPIParameters(
                    f"The subpath '{subpath}' should designate a subdirectory of the vfolder '{name}'.",
                )
            requested_mounts.append(req.ref)
            requested_mount_options[req.ref] = req.options
            requested_vfolder_names[req.ref] = name
            requested_vfolder_subpaths[req.ref] = os.path.normpath(subpath)
            _already_resolved.add(name)
            if req.dst_path is not None:
                requested_vfolder_dstpaths[req.ref] = req.dst_path

    # Check if there are overlapping mount sources
    for p1 in requested_mounts:
        for p2 in requested_mounts:
            if p1 == p2:
                continue
            if PurePosixPath(p1).is_relative_to(PurePosixPath(p2)):
                raise InvalidAPIParameters(
                    f"VFolder source path '{p1}' overlaps with '{p2}'",
                )

    # Fetch MODEL_STORE project IDs for cross-project mount allowance
    _ms_query = sa.select(groups_table.c.id).where(
        sa.and_(
            groups_table.c.domain_name == user_scope.domain_name,
            groups_table.c.type == DataProjectType.MODEL_STORE,
        )
    )
    _ms_result = await conn.execute(_ms_query)
    model_store_project_ids: set[str] = {str(row.id) for row in _ms_result.fetchall()}

    # Query the accessible vfolders that satisfy either:
    # - the name matches with the requested vfolder name, or
    # - the name starts with a dot (dot-prefixed vfolder) for automatic mounting.
    extra_vf_conds = vfolders.c.name.startswith(".")
    if requested_vfolder_names:
        extra_vf_conds = sa.or_(
            extra_vf_conds, vfolders.c.name.in_(requested_vfolder_names.values())
        )
    if requested_vfolder_ids:
        extra_vf_conds = sa.or_(
            extra_vf_conds,
            VFolderRow.id.in_(requested_vfolder_ids),
        )
    extra_vf_conds = sa.and_(extra_vf_conds, VFolderRow.status.not_in(DEAD_VFOLDER_STATUSES))
    accessible_vfolders = await query_accessible_vfolders(
        conn,
        user_scope.user_uuid,
        user_role=user_scope.user_role,
        domain_name=user_scope.domain_name,
        allowed_vfolder_types=allowed_vfolder_types,
        extra_vf_conds=extra_vf_conds,
    )

    # Fast-path for empty requested mounts
    if not accessible_vfolders:
        if requested_vfolder_names or requested_vfolder_ids:
            raise VFolderNotFound("There is no accessible vfolders at all.")
        return []

    requested_names = set(requested_vfolder_names.values())
    resolved_vfolder_ids: set[uuid.UUID] = set()
    for row in accessible_vfolders:
        vfid = row["id"]
        name = row["name"]
        if vfid in requested_vfolder_ids:
            resolved_vfolder_ids.add(vfid)
            # Bind every UUID-referenced request for this vfolder to its
            # resolved name. Each request keeps its own subpath/destination/
            # options (captured above), so multiple subpaths of one vfolder
            # all survive into the mount loop (lablup/backend.ai#11936). Source
            # overlap for these is enforced later by ``is_mount_duplicate``.
            for index in uuid_request_indices.get(vfid, ()):
                requested_vfolder_names[index] = name
            continue
        if name in _already_resolved:
            continue
        if name not in requested_names:
            requested_vfolder_names[vfid] = name
        requested_mounts.append(name)

    # A UUID-referenced request that matched no accessible vfolder would
    # otherwise be silently dropped (its index never enters the mount loop
    # below). Surface it like the name-referenced path does, so the caller
    # learns the requested mount was not honored (lablup/backend.ai#11936).
    if unresolved_vfolder_ids := (requested_vfolder_ids - resolved_vfolder_ids):
        raise VFolderNotFound(
            "VFolder(s) not found or accessible: "
            + ", ".join(sorted(str(vfid) for vfid in unresolved_vfolder_ids))
        )

    # Check if there are overlapping mount sources
    check_overlapping_mounts(requested_mounts)

    # add automount folder list into requested_vfolder_names
    # and requested_vfolder_subpath
    for _vfolder in accessible_vfolders:
        if _vfolder["name"].startswith("."):
            requested_vfolder_names.setdefault(_vfolder["id"], _vfolder["name"])
            requested_vfolder_subpaths.setdefault(_vfolder["id"], ".")

    # for vfolder in accessible_vfolders:
    accessible_vfolders_map = {vfolder["name"]: vfolder for vfolder in accessible_vfolders}
    for requested_key, vfolder_name in requested_vfolder_names.items():
        if not (vfolder := accessible_vfolders_map.get(vfolder_name)):
            raise VFolderNotFound(f"VFolder {vfolder_name} is not found or accessible.")
        try:
            await ensure_host_permission_allowed(
                conn,
                vfolder["host"],
                allowed_vfolder_types=allowed_vfolder_types,
                user_uuid=user_scope.user_uuid,
                resource_policy=resource_policy,
                domain_name=user_scope.domain_name,
                group_id=user_scope.group_id,
                permission=VFolderHostPermission.MOUNT_IN_SESSION,
            )
        except InsufficientStoragePermission as e:
            if vfolder["name"].startswith("."):
                log.warning(
                    "Skipping auto-mount VFolder '{}' due to insufficient permission",
                    vfolder["name"],
                )
                continue
            raise InsufficientStoragePermission(
                f"Permission denied to mount VFolder '{vfolder_name}' on host '{vfolder['host']}'. {e.extra_msg}",
                e.extra_data,
            ) from e
        if unmanaged_path := cast(str | None, vfolder["unmanaged_path"]):
            vfid = VFolderID(vfolder["quota_scope_id"], vfolder["id"])
            vfsubpath = PurePosixPath(".")
            if is_mount_duplicate(vfid, vfsubpath, matched_vfolder_mounts):
                continue
            kernel_path_raw = requested_vfolder_dstpaths.get(requested_key)
            if kernel_path_raw is None:
                kernel_path = PurePosixPath(f"/home/work/{vfolder['name']}")
            else:
                kernel_path = PurePosixPath(kernel_path_raw)
            matched_vfolder_mounts.append(
                VFolderMount(
                    name=vfolder["name"],
                    vfid=vfid,
                    vfsubpath=vfsubpath,
                    host_path=PurePosixPath(unmanaged_path),
                    kernel_path=kernel_path,
                    mount_perm=vfolder["permission"],
                    usage_mode=vfolder["usage_mode"],
                )
            )
            continue
        is_cross_project = vfolder["group"] is not None and vfolder["group"] != str(
            user_scope.group_id
        )
        is_model_store_vfolder = (
            vfolder["group"] is not None and vfolder["group"] in model_store_project_ids
        )
        if is_cross_project:
            if is_model_store_vfolder and vfolder["usage_mode"] == VFolderUsageMode.MODEL:
                pass  # Allow cross-project MODEL_STORE model vfolders (read-only)
            else:
                continue
        try:
            proxy_name, volume_name = storage_manager.get_proxy_and_volume(vfolder["host"])
            manager_client = storage_manager.get_manager_facing_client(proxy_name)
            mount_path_result = await manager_client.get_mount_path(
                volume_name,
                str(VFolderID(vfolder["quota_scope_id"], vfolder["id"])),
                str(PurePosixPath(requested_vfolder_subpaths[requested_key])),
            )
            mount_base_path = PurePosixPath(mount_path_result["path"])
        except VFolderOperationFailed as e:
            raise InvalidAPIParameters(e.extra_msg, e.extra_data) from None
        if (_vfname := vfolder["name"]) in VFOLDER_DSTPATHS_MAP:
            requested_vfolder_dstpaths[_vfname] = VFOLDER_DSTPATHS_MAP[_vfname]
        if vfolder["name"] == ".local" and vfolder["group"] is not None:
            vfid = VFolderID(vfolder["quota_scope_id"], vfolder["id"])
            vfsubpath = PurePosixPath(user_scope.user_uuid.hex)
            if is_mount_duplicate(vfid, vfsubpath, matched_vfolder_mounts):
                continue
            # Auto-create per-user subdirectory inside the group-owned ".local" vfolder.
            proxy_name, volume_name = storage_manager.get_proxy_and_volume(vfolder["host"])
            manager_client = storage_manager.get_manager_facing_client(proxy_name)
            await manager_client.mkdir(
                volume=volume_name,
                vfid=str(vfid),
                relpath=[vfsubpath.as_posix()],
                exist_ok=True,
            )
            # Mount the per-user subdirectory as the ".local" vfolder.
            matched_vfolder_mounts.append(
                VFolderMount(
                    name=vfolder["name"],
                    vfid=VFolderID(vfolder["quota_scope_id"], vfolder["id"]),
                    vfsubpath=PurePosixPath(user_scope.user_uuid.hex),
                    host_path=mount_base_path / user_scope.user_uuid.hex,
                    kernel_path=PurePosixPath("/home/work/.local"),
                    mount_perm=vfolder["permission"],
                    usage_mode=vfolder["usage_mode"],
                )
            )
        else:
            # Normal vfolders
            vfid = VFolderID(vfolder["quota_scope_id"], vfolder["id"])
            vfsubpath = PurePosixPath(requested_vfolder_subpaths[requested_key])
            if is_mount_duplicate(vfid, vfsubpath, matched_vfolder_mounts):
                continue
            kernel_path_raw = requested_vfolder_dstpaths.get(requested_key)
            if kernel_path_raw is None:
                kernel_path = PurePosixPath(f"/home/work/{vfolder['name']}")
            else:
                kernel_path = PurePosixPath(kernel_path_raw)
                if not kernel_path.is_absolute():
                    kernel_path = PurePosixPath("/home/work", kernel_path_raw)
            mount_opts = requested_mount_options.get(requested_key, VFolderMountOptions())
            if is_cross_project and is_model_store_vfolder:
                mount_perm = MountPermission.READ_ONLY
            else:
                match mount_opts.permission:
                    case MountPermission.READ_ONLY:
                        mount_perm = MountPermission.READ_ONLY
                    case MountPermission.READ_WRITE | MountPermission.RW_DELETE:
                        if vfolder["permission"] == VFolderPermission.READ_ONLY:
                            raise VFolderPermissionError(
                                f"VFolder {vfolder_name} is allowed to be accessed in '{vfolder['permission'].value}' mode, "
                                f"but attempted with '{mount_opts.permission.value}' mode."
                            )
                        mount_perm = mount_opts.permission
                    case _:  # None if unset
                        mount_perm = vfolder["permission"]

            matched_vfolder_mounts.append(
                VFolderMount(
                    name=vfolder["name"],
                    vfid=vfid,
                    vfsubpath=vfsubpath,
                    host_path=mount_base_path / vfsubpath,
                    kernel_path=kernel_path,
                    mount_perm=mount_perm,
                    usage_mode=vfolder["usage_mode"],
                )
            )

    # Check if there are overlapping mount targets
    check_overlapping_mounts([trgt.kernel_path for trgt in matched_vfolder_mounts])

    return matched_vfolder_mounts
