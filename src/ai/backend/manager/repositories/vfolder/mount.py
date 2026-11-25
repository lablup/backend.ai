from __future__ import annotations

import logging
import os.path
import uuid
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from pathlib import PurePosixPath
from typing import Any, Final

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import (
    MountPermission,
    VFolderHostPermission,
    VFolderID,
    VFolderMount,
    VFolderMountOptions,
    VFolderMountPolicy,
    VFolderMountRequest,
    VFolderUsageMode,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.project.types import ProjectType as DataProjectType
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus, VFolderOwnershipType
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import (
    InsufficientStoragePermission,
    VFolderNotFound,
    VFolderOperationFailed,
    VFolderPermissionError,
)
from ai.backend.manager.models.project.row import groups as groups_table
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.orders.condition import ConditionOrder
from ai.backend.manager.models.user.queries import joined_project_ids_query
from ai.backend.manager.models.vfolder.row import (
    VFolderRow,
    VFolderUserMountPolicyRow,
    vfolders,
)
from ai.backend.manager.models.vfolder.scopes import (
    ProjectVFolderTarget,
    UserVFolderTarget,
)
from ai.backend.manager.models.vfolder.searchable_fields import VFolderSearchableFields
from ai.backend.manager.repositories.vfolder.host_permission import ensure_host_permission_allowed
from ai.backend.manager.repositories.vfolder.mount_policy import resolve_mount_policy
from ai.backend.manager.types import UserScope

log = StructuredLogger(logging.getLogger(__spec__.name))

__all__: Sequence[str] = (
    "HeldPermissions",
    "drop_overlapping_auto_mounts",
    "prepare_auto_mounts",
    "prepare_vfolder_mounts",
    "query_reachable_vfolders",
)

_PROJECT_LOCAL_FOLDER_NAME: Final = ".local"

type HeldPermissions = Callable[
    [Sequence[VFolderUUID]], Awaitable[Mapping[EntityIdentifier, Permission]]
]


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


def check_overlapping_mounts(mounts: Iterable[str | PurePosixPath]) -> None:
    for p1 in mounts:
        for p2 in mounts:
            _p1 = PurePosixPath(p1)
            _p2 = PurePosixPath(p2)
            if _p1 == _p2:
                continue
            if _p1.is_relative_to(_p2):
                raise InvalidAPIParameters(
                    f"VFolder path '{_p1}' overlaps with '{_p2}'",
                )


def is_mount_duplicate(
    folder_id: VFolderID, subpath: PurePosixPath, mounts: Iterable[VFolderMount]
) -> bool:
    for mount in mounts:
        if mount.vfid != folder_id:
            continue
        if subpath.is_relative_to(mount.vfsubpath) or mount.vfsubpath.is_relative_to(subpath):
            return True
    return False


async def query_reachable_vfolders(
    conn: SAConnection,
    user_scope: UserScope,
    conditions: sa.ColumnElement[bool],
    held_permissions: HeldPermissions,
) -> list[dict[str, Any]]:
    """The vfolders matching ``conditions`` that the user's personal project or a joined
    project holds and the user may read, the session's project first.

    Each row carries the mount level the user gets on it: the folder's default, the
    user's own policy row over it, and read-write for the owner. ``none`` is kept on
    the row so a request naming the folder can be refused rather than not found.
    """
    user_id = UserID(user_scope.user_uuid)
    project_ids = (await conn.scalars(joined_project_ids_query(user_id))).all()
    scopes: list[OperationScope] = [UserVFolderTarget(user_id=user_id)]
    scopes.extend(ProjectVFolderTarget(project_id=pid) for pid in project_ids)
    membership = VFolderSearchableFields.linked.membership
    project_id = ProjectID(user_scope.group_id)
    rows = (
        await conn.execute(
            sa.select(vfolders)
            .where(conditions, sa.or_(*(scope.to_condition()() for scope in scopes)))
            .order_by(
                ConditionOrder(membership.reached_by(ProjectEntityType(), project_id)).first(),
                ConditionOrder(membership.shared_to(user_id)).last(),
            )
        )
    ).all()
    vfolder_ids = [VFolderUUID(row.id) for row in rows]
    held = await held_permissions(vfolder_ids)
    policies = {
        VFolderUUID(policy.vfolder_id): VFolderMountPolicy(policy.permission)
        for policy in (
            await conn.execute(
                sa.select(
                    VFolderUserMountPolicyRow.vfolder_id, VFolderUserMountPolicyRow.permission
                ).where(
                    VFolderUserMountPolicyRow.user_id == user_id,
                    VFolderUserMountPolicyRow.vfolder_id.in_(vfolder_ids),
                )
            )
        ).all()
    }
    reachable: list[dict[str, Any]] = []
    for row in rows:
        bits = held.get(VFolderUUID(row.id), Permission.NONE)
        if not bits.covers(Permission.READ):
            continue
        level = resolve_mount_policy(
            user_id,
            owner_user_id=row.user,
            default_mount_permission=row.default_mount_permission,
            held=bits,
            user_policy=policies.get(VFolderUUID(row.id)),
        )
        reachable.append({**row._mapping, "permission": level})
    return reachable


def _mount_unmanaged_vfolder(
    vfolder: Mapping[str, Any], kernel_path: PurePosixPath, mount_perm: MountPermission
) -> VFolderMount:
    return VFolderMount(
        name=vfolder["name"],
        vfid=VFolderID(vfolder["quota_scope_id"], vfolder["id"]),
        vfsubpath=PurePosixPath("."),
        host_path=PurePosixPath(vfolder["unmanaged_path"]),
        kernel_path=kernel_path,
        mount_perm=mount_perm,
        usage_mode=vfolder["usage_mode"],
    )


async def _get_mount_base_path(
    storage_manager: StorageSessionManager,
    vfolder: Mapping[str, Any],
    subpath: PurePosixPath,
) -> PurePosixPath:
    """The path the storage proxy mounts the folder's ``subpath`` from."""
    try:
        proxy_name, volume_name = storage_manager.get_proxy_and_volume(vfolder["host"])
        manager_client = storage_manager.get_manager_facing_client(proxy_name)
        mount_path_result = await manager_client.get_mount_path(
            volume_name,
            str(VFolderID(vfolder["quota_scope_id"], vfolder["id"])),
            str(subpath),
        )
    except VFolderOperationFailed as e:
        raise InvalidAPIParameters(e.extra_msg, e.extra_data) from None
    return PurePosixPath(mount_path_result["path"])


async def _mount_user_directory_of_project_local(
    storage_manager: StorageSessionManager,
    vfolder: Mapping[str, Any],
    user_id: uuid.UUID,
    mount_base_path: PurePosixPath,
) -> VFolderMount:
    """Mount the user's own directory of a project's ``.local`` folder, made if missing."""
    vfid = VFolderID(vfolder["quota_scope_id"], vfolder["id"])
    proxy_name, volume_name = storage_manager.get_proxy_and_volume(vfolder["host"])
    manager_client = storage_manager.get_manager_facing_client(proxy_name)
    await manager_client.mkdir(
        volume=volume_name,
        vfid=str(vfid),
        relpath=[user_id.hex],
        exist_ok=True,
    )
    return VFolderMount(
        name=vfolder["name"],
        vfid=vfid,
        vfsubpath=PurePosixPath(user_id.hex),
        host_path=mount_base_path / user_id.hex,
        kernel_path=PurePosixPath("/home/work", _PROJECT_LOCAL_FOLDER_NAME),
        mount_perm=MountPermission(vfolder["permission"].value),
        usage_mode=vfolder["usage_mode"],
    )


async def _may_auto_mount(
    conn: SAConnection,
    allowed_vfolder_types: Sequence[str],
    user_scope: UserScope,
    resource_policy: Mapping[str, Any],
    vfolder: Mapping[str, Any],
) -> bool:
    if vfolder["permission"] == VFolderMountPolicy.NONE:
        log.trace("auto-mount skipped, mount policy is none", vfolder_id=vfolder["id"])
        return False
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
    except InsufficientStoragePermission:
        log.trace("auto-mount skipped, host permission denied", vfolder_id=vfolder["id"])
        return False
    return True


async def prepare_auto_mounts(
    conn: SAConnection,
    storage_manager: StorageSessionManager,
    allowed_vfolder_types: Sequence[str],
    user_scope: UserScope,
    resource_policy: Mapping[str, Any],
    auto_mounts: Sequence[VFolderAutoMountData],
    held_permissions: HeldPermissions,
) -> Sequence[VFolderMount]:
    """The mounts of the session project's ``.local`` folder and of ``auto_mounts``, in that order.

    A folder the user cannot reach or may not mount is left out, and a read-only
    folder is mounted read-only whatever the auto-mount's own permission says.
    """
    reachable_vfolders = await query_reachable_vfolders(
        conn,
        user_scope,
        sa.and_(
            sa.or_(
                VFolderRow.id.in_([auto_mount.vfolder_id for auto_mount in auto_mounts]),
                sa.and_(
                    VFolderRow.name == _PROJECT_LOCAL_FOLDER_NAME,
                    VFolderRow.ownership_type == VFolderOwnershipType.GROUP,
                    VFolderRow.group == user_scope.group_id,
                ),
            ),
            VFolderRow.status.not_in(VFolderOperationStatus.dead()),
        ),
        held_permissions,
    )
    mountable_vfolders = {
        VFolderUUID(vfolder["id"]): vfolder
        for vfolder in reachable_vfolders
        if await _may_auto_mount(conn, allowed_vfolder_types, user_scope, resource_policy, vfolder)
    }
    mounts: list[VFolderMount] = []
    for vfolder in mountable_vfolders.values():
        if (
            vfolder["name"] != _PROJECT_LOCAL_FOLDER_NAME
            or vfolder["ownership_type"] != VFolderOwnershipType.GROUP
            or vfolder["group"] != user_scope.group_id
        ):
            continue
        if vfolder["unmanaged_path"]:
            mounts.append(
                _mount_unmanaged_vfolder(
                    vfolder,
                    PurePosixPath("/home/work", _PROJECT_LOCAL_FOLDER_NAME),
                    MountPermission(vfolder["permission"].value),
                )
            )
        else:
            mounts.append(
                await _mount_user_directory_of_project_local(
                    storage_manager,
                    vfolder,
                    user_scope.user_uuid,
                    await _get_mount_base_path(storage_manager, vfolder, PurePosixPath(".")),
                )
            )
    for auto_mount in auto_mounts:
        mountable_vfolder = mountable_vfolders.get(auto_mount.vfolder_id)
        if mountable_vfolder is None:
            continue
        kernel_path = PurePosixPath("/home/work", auto_mount.mount_destination)
        mount_perm = (
            MountPermission.READ_ONLY
            if mountable_vfolder["permission"] == VFolderMountPolicy.READ_ONLY
            else MountPermission(auto_mount.mount_permission.value)
        )
        if mountable_vfolder["unmanaged_path"]:
            mounts.append(_mount_unmanaged_vfolder(mountable_vfolder, kernel_path, mount_perm))
            continue
        subpath = PurePosixPath(_normalize_mount_subpath(auto_mount.subpath))
        mount_base_path = await _get_mount_base_path(storage_manager, mountable_vfolder, subpath)
        mounts.append(
            VFolderMount(
                name=mountable_vfolder["name"],
                vfid=VFolderID(mountable_vfolder["quota_scope_id"], mountable_vfolder["id"]),
                vfsubpath=subpath,
                host_path=mount_base_path / subpath,
                kernel_path=kernel_path,
                mount_perm=mount_perm,
                usage_mode=mountable_vfolder["usage_mode"],
            )
        )
    return mounts


def drop_overlapping_auto_mounts(
    auto_mounts: Sequence[VFolderMount], requested_mounts: Sequence[VFolderMount]
) -> Sequence[VFolderMount]:
    """The auto-mounts whose destination overlaps neither a requested mount nor an earlier one."""
    kept: list[VFolderMount] = []
    for auto_mount in auto_mounts:
        if any(
            auto_mount.kernel_path.is_relative_to(mount.kernel_path)
            or mount.kernel_path.is_relative_to(auto_mount.kernel_path)
            for mount in (*requested_mounts, *kept)
        ):
            log.trace(
                "auto-mount skipped, destination already used",
                vfolder_id=auto_mount.vfid.folder_id,
                mount_destination=str(auto_mount.kernel_path),
            )
            continue
        kept.append(auto_mount)
    return kept


async def prepare_vfolder_mounts(
    conn: SAConnection,
    storage_manager: StorageSessionManager,
    allowed_vfolder_types: Sequence[str],
    user_scope: UserScope,
    resource_policy: Mapping[str, Any],
    mount_requests: Sequence[VFolderMountRequest],
    held_permissions: HeldPermissions,
) -> Sequence[VFolderMount]:
    """
    Determine the actual mount information from the requested vfolder lists,
    vfolder configurations, and the given user scope.
    """
    if not mount_requests:
        return []
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
    model_store_project_ids: set[uuid.UUID] = {row.id for row in _ms_result.fetchall()}

    extra_vf_conds: sa.ColumnElement[bool] = sa.false()
    if requested_vfolder_names:
        extra_vf_conds = sa.or_(
            extra_vf_conds, vfolders.c.name.in_(requested_vfolder_names.values())
        )
    if requested_vfolder_ids:
        extra_vf_conds = sa.or_(
            extra_vf_conds,
            VFolderRow.id.in_(requested_vfolder_ids),
        )
    extra_vf_conds = sa.and_(
        extra_vf_conds, VFolderRow.status.not_in(VFolderOperationStatus.dead())
    )
    accessible_vfolders = await query_reachable_vfolders(
        conn, user_scope, extra_vf_conds, held_permissions
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

    # The session's project comes first, so its folder wins a name shared with another.
    accessible_vfolders_map: dict[str, dict[str, Any]] = {}
    for accessible_vfolder in accessible_vfolders:
        accessible_vfolders_map.setdefault(accessible_vfolder["name"], accessible_vfolder)
    for requested_key, vfolder_name in requested_vfolder_names.items():
        if not (vfolder := accessible_vfolders_map.get(vfolder_name)):
            raise VFolderNotFound(f"VFolder {vfolder_name} is not found or accessible.")
        if vfolder["permission"] == VFolderMountPolicy.NONE:
            raise VFolderPermissionError(f"VFolder {vfolder_name} is not permitted to be mounted.")
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
            raise InsufficientStoragePermission(
                f"Permission denied to mount VFolder '{vfolder_name}' on host '{vfolder['host']}'. {e.extra_msg}",
                e.extra_data,
            ) from e
        if vfolder["unmanaged_path"]:
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
                _mount_unmanaged_vfolder(
                    vfolder, kernel_path, MountPermission(vfolder["permission"].value)
                )
            )
            continue
        # A personal folder also carries a project — its owner's personal project — so
        # project ownership is read off the ownership type, never off the column.
        is_project_vfolder = vfolder["ownership_type"] == VFolderOwnershipType.GROUP
        is_cross_project = is_project_vfolder and vfolder["group"] != user_scope.group_id
        is_model_store_vfolder = is_project_vfolder and vfolder["group"] in model_store_project_ids
        if is_cross_project:
            if is_model_store_vfolder and vfolder["usage_mode"] == VFolderUsageMode.MODEL:
                pass  # Allow cross-project MODEL_STORE model vfolders (read-only)
            else:
                continue
        mount_base_path = await _get_mount_base_path(
            storage_manager, vfolder, PurePosixPath(requested_vfolder_subpaths[requested_key])
        )
        if vfolder["name"] == _PROJECT_LOCAL_FOLDER_NAME and is_project_vfolder:
            vfid = VFolderID(vfolder["quota_scope_id"], vfolder["id"])
            vfsubpath = PurePosixPath(user_scope.user_uuid.hex)
            if is_mount_duplicate(vfid, vfsubpath, matched_vfolder_mounts):
                continue
            matched_vfolder_mounts.append(
                await _mount_user_directory_of_project_local(
                    storage_manager, vfolder, user_scope.user_uuid, mount_base_path
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
                        if vfolder["permission"] == VFolderMountPolicy.READ_ONLY:
                            raise VFolderPermissionError(
                                f"VFolder {vfolder_name} is allowed to be accessed in '{vfolder['permission'].value}' mode, "
                                f"but attempted with '{mount_opts.permission.value}' mode."
                            )
                        mount_perm = mount_opts.permission
                    case _:  # None if unset
                        mount_perm = MountPermission(vfolder["permission"].value)

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
