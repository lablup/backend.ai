from __future__ import annotations

import enum
import logging
import os.path
import uuid
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any, List, Mapping, NamedTuple, Optional, Sequence

import aiohttp
import aiotools
import graphene
import sqlalchemy as sa
import trafaret as t
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.bgtask import ProgressReporter
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)

from ..api.exceptions import InvalidAPIParameters, VFolderNotFound, VFolderOperationFailed
from ..defs import RESERVED_VFOLDER_PATTERNS, RESERVED_VFOLDERS, VFOLDER_DSTPATHS_MAP
from ..types import UserScope
from .base import (
    GUID,
    Base,
    BigInt,
    EnumValueType,
    IDColumn,
    Item,
    PaginatedList,
    QuotaScopeIDType,
    batch_multiresult,
    metadata,
)
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser, enum_field_getter
from .user import UserRole
from .utils import ExtendedAsyncSAEngine, execute_with_retry

if TYPE_CHECKING:
    from ..api.context import BackgroundTaskManager
    from .gql import GraphQueryContext
    from .storage import StorageSessionManager

__all__: Sequence[str] = (
    "vfolders",
    "vfolder_invitations",
    "vfolder_permissions",
    "VirtualFolder",
    "VFolderOwnershipType",
    "VFolderInvitationState",
    "VFolderPermission",
    "VFolderPermissionValidator",
    "VFolderOperationStatus",
    "VFolderAccessStatus",
    "VFolderCloneInfo",
    "VFolderDeletionInfo",
    "VFolderRow",
    "QuotaScope",
    "SetQuotaScope",
    "UnsetQuotaScope",
    "query_accessible_vfolders",
    "initiate_vfolder_clone",
    "initiate_vfolder_removal",
    "get_allowed_vfolder_hosts_by_group",
    "get_allowed_vfolder_hosts_by_user",
    "verify_vfolder_name",
    "prepare_vfolder_mounts",
    "filter_host_allowed_permission",
    "ensure_host_permission_allowed",
)


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class VFolderOwnershipType(str, enum.Enum):
    """
    Ownership type of virtual folder.
    """

    USER = "user"
    GROUP = "group"


class VFolderPermission(str, enum.Enum):
    """
    Permissions for a virtual folder given to a specific access key.
    RW_DELETE includes READ_WRITE and READ_WRITE includes READ_ONLY.
    """

    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"  # resolved as RW_DELETE


class VFolderPermissionValidator(t.Trafaret):
    def check_and_return(self, value: Any) -> VFolderPermission:
        if value not in ["ro", "rw", "wd"]:
            self._failure('one of "ro", "rw", or "wd" required', value=value)
        return VFolderPermission(value)


class VFolderInvitationState(str, enum.Enum):
    """
    Virtual Folder invitation state.
    """

    PENDING = "pending"
    CANCELED = "canceled"  # canceled by inviter
    ACCEPTED = "accepted"
    REJECTED = "rejected"  # rejected by invitee


class VFolderOperationStatus(str, enum.Enum):
    """
    Introduce virtual folder current status for storage-proxy operations.
    """

    READY = "ready"
    PERFORMING = "performing"
    CLONING = "cloning"
    DELETING = "deleting"
    MOUNTED = "mounted"


class VFolderAccessStatus(str, enum.Enum):
    """
    Introduce virtual folder desired status for storage-proxy operations.
    Not added to db scheme  and determined only by current vfolder status.
    """

    READABLE = "readable"
    UPDATABLE = "updatable"
    DELETABLE = "deletable"


class VFolderDeletionInfo(NamedTuple):
    vfolder_id: VFolderID
    host: str


class VFolderCloneInfo(NamedTuple):
    source_vfolder_id: VFolderID
    source_host: str

    # Target Vfolder infos
    target_quota_scope_id: str
    target_vfolder_name: str
    target_host: str
    usage_mode: VFolderUsageMode
    permission: VFolderPermission
    email: str
    user_id: uuid.UUID
    cloneable: bool


vfolders = sa.Table(
    "vfolders",
    metadata,
    IDColumn("id"),
    # host will be '' if vFolder is unmanaged
    sa.Column("host", sa.String(length=128), nullable=False),
    sa.Column("quota_scope_id", QuotaScopeIDType, nullable=False),
    sa.Column("name", sa.String(length=64), nullable=False, index=True),
    sa.Column(
        "usage_mode",
        EnumValueType(VFolderUsageMode),
        default=VFolderUsageMode.GENERAL,
        nullable=False,
    ),
    sa.Column("permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE),
    sa.Column("max_files", sa.Integer(), default=1000),
    sa.Column("max_size", sa.Integer(), default=None),  # in MBytes
    sa.Column("num_files", sa.Integer(), default=0),
    sa.Column("cur_size", sa.Integer(), default=0),  # in KBytes
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
    # creator is always set to the user who created vfolder (regardless user/project types)
    sa.Column("creator", sa.String(length=128), nullable=True),
    # unmanaged vfolder represents the host-side absolute path instead of storage-based path.
    sa.Column("unmanaged_path", sa.String(length=512), nullable=True),
    sa.Column(
        "ownership_type",
        EnumValueType(VFolderOwnershipType),
        default=VFolderOwnershipType.USER,
        nullable=False,
    ),
    sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=True),  # owner if user vfolder
    sa.Column("group", GUID, sa.ForeignKey("groups.id"), nullable=True),  # owner if project vfolder
    sa.Column("cloneable", sa.Boolean, default=False, nullable=False),
    sa.Column(
        "status",
        EnumValueType(VFolderOperationStatus),
        default=VFolderOperationStatus.READY,
        server_default=VFolderOperationStatus.READY.value,
        nullable=False,
    ),
    sa.CheckConstraint(
        "(ownership_type = 'user' AND \"user\" IS NOT NULL) OR "
        "(ownership_type = 'group' AND \"group\" IS NOT NULL)",
        name="ownership_type_match_with_user_or_group",
    ),
    sa.CheckConstraint(
        '("user" IS NULL AND "group" IS NOT NULL) OR ("user" IS NOT NULL AND "group" IS NULL)',
        name="either_one_of_user_or_group",
    ),
)


vfolder_attachment = sa.Table(
    "vfolder_attachment",
    metadata,
    sa.Column(
        "vfolder",
        GUID,
        sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "kernel",
        GUID,
        sa.ForeignKey("kernels.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.PrimaryKeyConstraint("vfolder", "kernel"),
)


vfolder_invitations = sa.Table(
    "vfolder_invitations",
    metadata,
    IDColumn("id"),
    sa.Column("permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE),
    sa.Column("inviter", sa.String(length=256)),  # email
    sa.Column("invitee", sa.String(length=256), nullable=False),  # email
    sa.Column(
        "state", EnumValueType(VFolderInvitationState), default=VFolderInvitationState.PENDING
    ),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        nullable=True,
        onupdate=sa.func.current_timestamp(),
    ),
    sa.Column(
        "vfolder",
        GUID,
        sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
)


vfolder_permissions = sa.Table(
    "vfolder_permissions",
    metadata,
    sa.Column("permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE),
    sa.Column(
        "vfolder",
        GUID,
        sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=False),
)


class VFolderRow(Base):
    __table__ = vfolders


def verify_vfolder_name(folder: str) -> bool:
    if folder in RESERVED_VFOLDERS:
        return False
    for pattern in RESERVED_VFOLDER_PATTERNS:
        if pattern.match(folder):
            return False
    return True


async def query_accessible_vfolders(
    conn: SAConnection,
    user_uuid: uuid.UUID,
    *,
    # when enabled, skip vfolder ownership check if user role is admin or superadmin
    allow_privileged_access=False,
    user_role=None,
    domain_name=None,
    allowed_vfolder_types=None,
    extra_vf_conds=None,
    extra_invited_vf_conds=None,
    extra_vf_user_conds=None,
    extra_vf_group_conds=None,
) -> Sequence[Mapping[str, Any]]:
    from ai.backend.manager.models import association_groups_users as agus
    from ai.backend.manager.models import groups, users

    if allowed_vfolder_types is None:
        allowed_vfolder_types = ["user"]  # legacy default

    vfolders_selectors = [
        vfolders.c.name,
        vfolders.c.id,
        vfolders.c.host,
        vfolders.c.quota_scope_id,
        vfolders.c.usage_mode,
        vfolders.c.created_at,
        vfolders.c.last_used,
        vfolders.c.max_files,
        vfolders.c.max_size,
        vfolders.c.ownership_type,
        vfolders.c.user,
        vfolders.c.group,
        vfolders.c.creator,
        vfolders.c.unmanaged_path,
        vfolders.c.cloneable,
        vfolders.c.status,
        vfolders.c.cur_size,
        # vfolders.c.permission,
        # users.c.email,
    ]

    async def _append_entries(_query, _is_owner=True):
        if extra_vf_conds is not None:
            _query = _query.where(extra_vf_conds)
        if extra_vf_user_conds is not None:
            _query = _query.where(extra_vf_user_conds)
        result = await conn.execute(_query)
        for row in result:
            row_keys = row.keys()
            _perm = (
                row.vfolder_permissions_permission
                if "vfolder_permissions_permission" in row_keys
                else row.vfolders_permission
            )
            entries.append(
                {
                    "name": row.vfolders_name,
                    "id": row.vfolders_id,
                    "host": row.vfolders_host,
                    "quota_scope_id": row.vfolders_quota_scope_id,
                    "usage_mode": row.vfolders_usage_mode,
                    "created_at": row.vfolders_created_at,
                    "last_used": row.vfolders_last_used,
                    "max_size": row.vfolders_max_size,
                    "max_files": row.vfolders_max_files,
                    "ownership_type": row.vfolders_ownership_type,
                    "user": str(row.vfolders_user) if row.vfolders_user else None,
                    "group": str(row.vfolders_group) if row.vfolders_group else None,
                    "creator": row.vfolders_creator,
                    "user_email": row.users_email if "users_email" in row_keys else None,
                    "group_name": row.groups_name if "groups_name" in row_keys else None,
                    "is_owner": _is_owner,
                    "permission": _perm,
                    "unmanaged_path": row.vfolders_unmanaged_path,
                    "cloneable": row.vfolders_cloneable,
                    "status": row.vfolders_status,
                    "cur_size": row.vfolders_cur_size,
                }
            )

    entries: List[dict] = []
    # User vfolders.
    if "user" in allowed_vfolder_types:
        # Scan my owned vfolders.
        j = vfolders.join(users, vfolders.c.user == users.c.uuid)
        query = sa.select(
            vfolders_selectors + [vfolders.c.permission, users.c.email], use_labels=True
        ).select_from(j)
        if not allow_privileged_access or (
            user_role != UserRole.ADMIN and user_role != UserRole.SUPERADMIN
        ):
            query = query.where(vfolders.c.user == user_uuid)
        await _append_entries(query)

        # Scan vfolders shared with me.
        j = vfolders.join(
            vfolder_permissions,
            vfolders.c.id == vfolder_permissions.c.vfolder,
            isouter=True,
        ).join(
            users,
            vfolders.c.user == users.c.uuid,
            isouter=True,
        )
        query = (
            sa.select(
                vfolders_selectors + [vfolder_permissions.c.permission, users.c.email],
                use_labels=True,
            )
            .select_from(j)
            .where(
                (vfolder_permissions.c.user == user_uuid)
                & (vfolders.c.ownership_type == VFolderOwnershipType.USER),
            )
        )
        if extra_invited_vf_conds is not None:
            query = query.where(extra_invited_vf_conds)
        await _append_entries(query, _is_owner=False)

    if "group" in allowed_vfolder_types:
        # Scan group vfolders.
        if user_role == UserRole.ADMIN or user_role == "admin":
            query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == domain_name)
            )
            result = await conn.execute(query)
            grps = result.fetchall()
            group_ids = [g.id for g in grps]
        else:
            j = sa.join(agus, users, agus.c.user_id == users.c.uuid)
            query = sa.select([agus.c.group_id]).select_from(j).where(agus.c.user_id == user_uuid)
            result = await conn.execute(query)
            grps = result.fetchall()
            group_ids = [g.group_id for g in grps]
        j = vfolders.join(groups, vfolders.c.group == groups.c.id)
        query = sa.select(
            vfolders_selectors + [vfolders.c.permission, groups.c.name], use_labels=True
        ).select_from(j)
        if user_role != UserRole.SUPERADMIN and user_role != "superadmin":
            query = query.where(vfolders.c.group.in_(group_ids))
        if extra_vf_group_conds is not None:
            query = query.where(extra_vf_group_conds)
        is_owner = (user_role == UserRole.ADMIN or user_role == "admin") or (
            user_role == UserRole.SUPERADMIN or user_role == "superadmin"
        )
        await _append_entries(query, is_owner)

        # Override permissions, if exists, for group vfolders.
        j = sa.join(
            vfolders,
            vfolder_permissions,
            vfolders.c.id == vfolder_permissions.c.vfolder,
        )
        query = (
            sa.select(vfolder_permissions.c.permission, vfolder_permissions.c.vfolder)
            .select_from(j)
            .where(
                (vfolders.c.group.in_(group_ids)) & (vfolder_permissions.c.user == user_uuid),
            )
        )
        if extra_vf_conds is not None:
            query = query.where(extra_vf_conds)
        if extra_vf_user_conds is not None:
            query = query.where(extra_vf_user_conds)
        result = await conn.execute(query)
        overriding_permissions: dict = {row.vfolder: row.permission for row in result}
        for entry in entries:
            if (
                entry["id"] in overriding_permissions
                and entry["ownership_type"] == VFolderOwnershipType.GROUP
            ):
                entry["permission"] = overriding_permissions[entry["id"]]

    return entries


async def get_allowed_vfolder_hosts_by_group(
    conn: SAConnection,
    resource_policy,
    domain_name: str,
    group_id: Optional[uuid.UUID] = None,
    domain_admin: bool = False,
) -> VFolderHostPermissionMap:
    """
    Union `allowed_vfolder_hosts` from domain, group, and keypair_resource_policy.

    If `group_id` is not None, `allowed_vfolder_hosts` from the group is also merged.
    If the requester is a domain admin, gather all `allowed_vfolder_hosts` of the domain groups.
    """
    from . import domains, groups

    # Domain's allowed_vfolder_hosts.
    allowed_hosts = VFolderHostPermissionMap()
    query = sa.select([domains.c.allowed_vfolder_hosts]).where(
        (domains.c.name == domain_name) & (domains.c.is_active),
    )
    if values := await conn.scalar(query):
        allowed_hosts = allowed_hosts | values
    # Group's allowed_vfolder_hosts.
    if group_id is not None:
        query = sa.select([groups.c.allowed_vfolder_hosts]).where(
            (groups.c.domain_name == domain_name)
            & (groups.c.id == group_id)
            & (groups.c.is_active),
        )
        if values := await conn.scalar(query):
            allowed_hosts = allowed_hosts | values
    elif domain_admin:
        query = sa.select([groups.c.allowed_vfolder_hosts]).where(
            (groups.c.domain_name == domain_name) & (groups.c.is_active),
        )
        if rows := (await conn.execute(query)).fetchall():
            for row in rows:
                allowed_hosts = allowed_hosts | row.allowed_vfolder_hosts
    # Keypair Resource Policy's allowed_vfolder_hosts
    allowed_hosts = allowed_hosts | resource_policy["allowed_vfolder_hosts"]
    return allowed_hosts


async def get_allowed_vfolder_hosts_by_user(
    conn: SAConnection,
    resource_policy: Mapping[str, Any],
    domain_name: str,
    user_uuid: uuid.UUID,
    group_id: Optional[uuid.UUID] = None,
) -> VFolderHostPermissionMap:
    """
    Union `allowed_vfolder_hosts` from domain, groups, and keypair_resource_policy.

    All available `allowed_vfolder_hosts` of groups which requester associated will be merged.
    """
    from . import association_groups_users, domains, groups

    # Domain's allowed_vfolder_hosts.
    allowed_hosts = VFolderHostPermissionMap()
    query = sa.select([domains.c.allowed_vfolder_hosts]).where(
        (domains.c.name == domain_name) & (domains.c.is_active),
    )
    if values := await conn.scalar(query):
        allowed_hosts = allowed_hosts | values
    # User's Groups' allowed_vfolder_hosts.
    if group_id is not None:
        j = groups.join(
            association_groups_users,
            (
                (groups.c.id == association_groups_users.c.group_id)
                & (groups.c.id == group_id)
                & (association_groups_users.c.user_id == user_uuid)
            ),
        )
    else:
        j = groups.join(
            association_groups_users,
            (
                (groups.c.id == association_groups_users.c.group_id)
                & (association_groups_users.c.user_id == user_uuid)
            ),
        )
    query = (
        sa.select([groups.c.allowed_vfolder_hosts])
        .select_from(j)
        .where(
            (groups.c.domain_name == domain_name) & (groups.c.is_active),
        )
    )
    if rows := (await conn.execute(query)).fetchall():
        for row in rows:
            allowed_hosts = allowed_hosts | row.allowed_vfolder_hosts
    # Keypair Resource Policy's allowed_vfolder_hosts
    allowed_hosts = allowed_hosts | resource_policy["allowed_vfolder_hosts"]
    return allowed_hosts


async def prepare_vfolder_mounts(
    conn: SAConnection,
    storage_manager: StorageSessionManager,
    allowed_vfolder_types: Sequence[str],
    user_scope: UserScope,
    resource_policy: Mapping[str, Any],
    requested_mount_references: Sequence[str | uuid.UUID],
    requested_mount_reference_map: Mapping[str | uuid.UUID, str],
) -> Sequence[VFolderMount]:
    """
    Determine the actual mount information from the requested vfolder lists,
    vfolder configurations, and the given user scope.
    """
    requested_mounts: list[str] = [
        name for name in requested_mount_references if isinstance(name, str)
    ]
    requested_mount_map: dict[str, str] = {
        name: path for name, path in requested_mount_reference_map.items() if isinstance(name, str)
    }

    vfolder_ids_to_resolve = [
        vfid for vfid in requested_mount_references if isinstance(vfid, uuid.UUID)
    ]
    query = (
        sa.select([vfolders.c.id, vfolders.c.name])
        .select_from(vfolders)
        .where(vfolders.c.id.in_(vfolder_ids_to_resolve))
    )
    result = await conn.execute(query)

    for vfid, name in result.fetchall():
        requested_mounts.append(name)
        if path := requested_mount_reference_map.get(vfid):
            requested_mount_map[name] = path

    requested_vfolder_names: dict[str, str] = {}
    requested_vfolder_subpaths: dict[str, str] = {}
    requested_vfolder_dstpaths: dict[str, str] = {}
    matched_vfolder_mounts: list[VFolderMount] = []

    # Split the vfolder name and subpaths
    for key in requested_mounts:
        name, _, subpath = key.partition("/")
        if not PurePosixPath(os.path.normpath(key)).is_relative_to(name):
            raise InvalidAPIParameters(
                f"The subpath '{subpath}' should designate a subdirectory of the vfolder '{name}'.",
            )
        requested_vfolder_names[key] = name
        requested_vfolder_subpaths[key] = os.path.normpath(subpath)
    for key, value in requested_mount_map.items():
        requested_vfolder_dstpaths[key] = value

    # Check if there are overlapping mount sources
    for p1 in requested_mounts:
        for p2 in requested_mounts:
            if p1 == p2:
                continue
            if PurePosixPath(p1).is_relative_to(PurePosixPath(p2)):
                raise InvalidAPIParameters(
                    f"VFolder source path '{p1}' overlaps with '{p2}'",
                )

    # Query the accessible vfolders that satisfy either:
    # - the name matches with the requested vfolder name, or
    # - the name starts with a dot (dot-prefixed vfolder) for automatic mounting.
    if requested_vfolder_names:
        extra_vf_conds = vfolders.c.name.in_(
            requested_vfolder_names.values()
        ) | vfolders.c.name.startswith(".")
    else:
        extra_vf_conds = vfolders.c.name.startswith(".")
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
        if requested_vfolder_names:
            raise VFolderNotFound("There is no accessible vfolders at all.")
        else:
            return []
    accessible_vfolders_map = {vfolder["name"]: vfolder for vfolder in accessible_vfolders}

    # add automount folder list into requested_vfolder_names
    # and requested_vfolder_subpath
    for _vfolder in accessible_vfolders:
        if _vfolder["name"].startswith("."):
            requested_vfolder_names.setdefault(_vfolder["name"], _vfolder["name"])
            requested_vfolder_subpaths.setdefault(_vfolder["name"], ".")

    # for vfolder in accessible_vfolders:
    for key, vfolder_name in requested_vfolder_names.items():
        if not (vfolder := accessible_vfolders_map.get(vfolder_name)):
            raise VFolderNotFound(f"VFolder {vfolder_name} is not found or accessible.")
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
        if vfolder["group"] is not None and vfolder["group"] != str(user_scope.group_id):
            # User's accessible group vfolders should not be mounted
            # if they do not belong to the execution kernel.
            continue
        try:
            mount_base_path = PurePosixPath(
                await storage_manager.get_mount_path(
                    vfolder["host"],
                    VFolderID(vfolder["quota_scope_id"], vfolder["id"]),
                    PurePosixPath(requested_vfolder_subpaths[key]),
                ),
            )
        except VFolderOperationFailed as e:
            raise InvalidAPIParameters(e.extra_msg, e.extra_data) from None
        if (_vfname := vfolder["name"]) in VFOLDER_DSTPATHS_MAP:
            requested_vfolder_dstpaths[_vfname] = VFOLDER_DSTPATHS_MAP[_vfname]
        if vfolder["name"] == ".local" and vfolder["group"] is not None:
            # Auto-create per-user subdirectory inside the group-owned ".local" vfolder.
            async with storage_manager.request(
                vfolder["host"],
                "POST",
                "folder/file/mkdir",
                params={
                    "volume": storage_manager.split_host(vfolder["host"])[1],
                    "vfid": str(VFolderID(vfolder["quota_scope_id"], vfolder["id"])),
                    "relpath": str(user_scope.user_uuid.hex),
                    "exist_ok": True,
                },
            ):
                pass
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
            kernel_path_raw = requested_vfolder_dstpaths.get(key)
            if kernel_path_raw is None:
                kernel_path = PurePosixPath(f"/home/work/{vfolder['name']}")
            else:
                kernel_path = PurePosixPath(kernel_path_raw)
                if not kernel_path.is_absolute():
                    kernel_path = PurePosixPath("/home/work", kernel_path_raw)
            matched_vfolder_mounts.append(
                VFolderMount(
                    name=vfolder["name"],
                    vfid=VFolderID(vfolder["quota_scope_id"], vfolder["id"]),
                    vfsubpath=PurePosixPath(requested_vfolder_subpaths[key]),
                    host_path=mount_base_path / requested_vfolder_subpaths[key],
                    kernel_path=kernel_path,
                    mount_perm=vfolder["permission"],
                    usage_mode=vfolder["usage_mode"],
                )
            )

    # Check if there are overlapping mount targets
    for vf1 in matched_vfolder_mounts:
        for vf2 in matched_vfolder_mounts:
            if vf1.name == vf2.name:
                continue
            if vf1.kernel_path.is_relative_to(vf2.kernel_path):
                raise InvalidAPIParameters(
                    f"VFolder mount path {vf1.kernel_path} overlaps with {vf2.kernel_path}",
                )

    return matched_vfolder_mounts


async def ensure_host_permission_allowed(
    db_conn,
    folder_host: str,
    *,
    permission: VFolderHostPermission,
    allowed_vfolder_types: Sequence[str],
    user_uuid: uuid.UUID,
    resource_policy: Mapping[str, Any],
    domain_name: str,
    group_id: Optional[uuid.UUID] = None,
) -> None:
    allowed_hosts = await filter_host_allowed_permission(
        db_conn,
        allowed_vfolder_types=allowed_vfolder_types,
        user_uuid=user_uuid,
        resource_policy=resource_policy,
        domain_name=domain_name,
        group_id=group_id,
    )
    if folder_host not in allowed_hosts or permission not in allowed_hosts[folder_host]:
        raise InvalidAPIParameters(f"`{permission}` Not allowed in vfolder host(`{folder_host}`)")


async def filter_host_allowed_permission(
    db_conn,
    *,
    allowed_vfolder_types: Sequence[str],
    user_uuid: uuid.UUID,
    resource_policy: Mapping[str, Any],
    domain_name: str,
    group_id: Optional[uuid.UUID] = None,
) -> VFolderHostPermissionMap:
    allowed_hosts = VFolderHostPermissionMap()
    if "user" in allowed_vfolder_types:
        allowed_hosts_by_user = await get_allowed_vfolder_hosts_by_user(
            db_conn, resource_policy, domain_name, user_uuid
        )
        allowed_hosts = allowed_hosts | allowed_hosts_by_user
    if "group" in allowed_vfolder_types and group_id is not None:
        allowed_hosts_by_group = await get_allowed_vfolder_hosts_by_group(
            db_conn, resource_policy, domain_name, group_id
        )
        allowed_hosts = allowed_hosts | allowed_hosts_by_group
    return allowed_hosts


async def initiate_vfolder_clone(
    db_engine: ExtendedAsyncSAEngine,
    vfolder_info: VFolderCloneInfo,
    storage_manager: StorageSessionManager,
    background_task_manager: BackgroundTaskManager,
) -> tuple[uuid.UUID, uuid.UUID]:
    source_vf_cond = vfolders.c.id == vfolder_info.source_vfolder_id.folder_id

    async def _update_status() -> None:
        async with db_engine.begin_session() as db_session:
            query = (
                sa.update(vfolders)
                .values(status=VFolderOperationStatus.CLONING)
                .where(source_vf_cond)
            )
            await db_session.execute(query)

    await execute_with_retry(_update_status)

    target_proxy, target_volume = storage_manager.split_host(vfolder_info.target_host)
    source_proxy, source_volume = storage_manager.split_host(vfolder_info.source_host)

    # Generate the ID of the destination vfolder.
    # TODO: If we refactor to use ORM, the folder ID will be created from the database by inserting
    #       the actual object (with RETURNING clause).  In that case, we need to temporarily
    #       mark the object to be "unusable-yet" until the storage proxy craetes the destination
    #       vfolder.  After done, we need to make another transaction to clear the unusable state.
    target_folder_id = VFolderID(vfolder_info.source_vfolder_id.quota_scope_id, uuid.uuid4())

    async def _clone(reporter: ProgressReporter) -> None:
        async def _insert_vfolder() -> None:
            async with db_engine.begin_session() as db_session:
                insert_values = {
                    "id": target_folder_id.folder_id,
                    "name": vfolder_info.target_vfolder_name,
                    "usage_mode": vfolder_info.usage_mode,
                    "permission": vfolder_info.permission,
                    "last_used": None,
                    "host": vfolder_info.target_host,
                    # TODO: add quota_scope_id
                    "creator": vfolder_info.email,
                    "ownership_type": VFolderOwnershipType("user"),
                    "user": vfolder_info.user_id,
                    "group": None,
                    "unmanaged_path": "",
                    "cloneable": vfolder_info.cloneable,
                    "quota_scope_id": vfolder_info.source_vfolder_id.quota_scope_id,
                }
                insert_query = sa.insert(vfolders, insert_values)
                try:
                    await db_session.execute(insert_query)
                except sa.exc.DataError:
                    # TODO: pass exception info
                    raise InvalidAPIParameters

        await execute_with_retry(_insert_vfolder)

        try:
            async with storage_manager.request(
                source_proxy,
                "POST",
                "folder/clone",
                json={
                    "src_volume": source_volume,
                    "src_vfid": str(vfolder_info.source_vfolder_id),
                    "dst_volume": target_volume,
                    "dst_vfid": str(target_folder_id),
                },
            ):
                pass
        except aiohttp.ClientResponseError:
            raise VFolderOperationFailed(extra_msg=str(vfolder_info.source_vfolder_id))

        async def _update_source_vfolder() -> None:
            async with db_engine.begin_session() as db_session:
                query = (
                    sa.update(vfolders)
                    .values(status=VFolderOperationStatus.READY)
                    .where(source_vf_cond)
                )
                await db_session.execute(query)

        await execute_with_retry(_update_source_vfolder)

    task_id = await background_task_manager.start(_clone)
    return task_id, target_folder_id.folder_id


async def initiate_vfolder_removal(
    db_engine: ExtendedAsyncSAEngine,
    requested_vfolders: Sequence[VFolderDeletionInfo],
    storage_manager: StorageSessionManager,
    storage_ptask_group: aiotools.PersistentTaskGroup,
) -> int:
    vfolder_info_len = len(requested_vfolders)
    vfolder_ids = tuple(vf_id.folder_id for vf_id, _ in requested_vfolders)
    cond = vfolders.c.id.in_(vfolder_ids)
    if vfolder_info_len == 0:
        return 0
    elif vfolder_info_len == 1:
        cond = vfolders.c.id == vfolder_ids[0]

    async def _update_vfolder_status() -> None:
        async with db_engine.begin_session() as db_session:
            query = sa.update(vfolders).values(status=VFolderOperationStatus.DELETING).where(cond)
            await db_session.execute(query)

    await execute_with_retry(_update_vfolder_status)

    row_deletion_infos: list[VFolderDeletionInfo] = []
    failed_deletion: list[tuple[VFolderDeletionInfo, str]] = []

    async def _delete():
        for vfolder_info in requested_vfolders:
            folder_id, host_name = vfolder_info
            proxy_name, volume_name = storage_manager.split_host(host_name)
            try:
                async with storage_manager.request(
                    proxy_name,
                    "POST",
                    "folder/delete",
                    json={
                        "volume": volume_name,
                        "vfid": str(folder_id),
                    },
                ) as (_, resp):
                    pass
            except (VFolderOperationFailed, InvalidAPIParameters) as e:
                if e.status == 404:
                    row_deletion_infos.append(vfolder_info)
                else:
                    failed_deletion.append((vfolder_info, repr(e)))
            except Exception as e:
                failed_deletion.append((vfolder_info, repr(e)))
            else:
                row_deletion_infos.append(vfolder_info)
        if row_deletion_infos:
            vfolder_ids = tuple(vf_id.folder_id for vf_id, _ in row_deletion_infos)

            async def _delete_row() -> None:
                async with db_engine.begin_session() as db_session:
                    await db_session.execute(
                        sa.delete(vfolders).where(vfolders.c.id.in_(vfolder_ids))
                    )

            await execute_with_retry(_delete_row)
            log.debug("Successfully removed vfolders {}", [str(x) for x in vfolder_ids])
        if failed_deletion:
            extra_data = {str(vfid.vfolder_id): err_msg for vfid, err_msg in failed_deletion}
            raise VFolderOperationFailed(extra_data=extra_data)

    storage_ptask_group.create_task(_delete(), name="delete_vfolders")
    log.debug("Started removing vFolders {}", [str(x) for x in vfolder_ids])

    return vfolder_info_len


async def ensure_quota_scope_accessible_by_user(
    conn: SASession,
    quota_scope: QuotaScopeID,
    user: Mapping[str, Any],
) -> None:
    from ai.backend.manager.models import GroupRow, UserRow
    from ai.backend.manager.models import association_groups_users as agus

    # Lookup user table to match if quota is scoped to the user
    query = sa.select(UserRow).where(UserRow.uuid == quota_scope.scope_id)
    quota_scope_user = await conn.scalar(query)
    if quota_scope_user:
        match user["role"]:
            case UserRole.SUPERADMIN:
                return
            case UserRole.ADMIN:
                if quota_scope_user.domain == user["domain"]:
                    return
            case _:
                if quota_scope_user.uuid == user["uuid"]:
                    return
        raise InvalidAPIParameters

    # Lookup group table to match if quota is scoped to the group
    query = sa.select(GroupRow).where(GroupRow.id == quota_scope.scope_id)
    quota_scope_group = await conn.scalar(query)
    if quota_scope_group:
        match user["role"]:
            case UserRole.SUPERADMIN:
                return
            case UserRole.ADMIN:
                if quota_scope_group.domain == user["domain"]:
                    return
            case _:
                query = (
                    sa.select([agus.c.group_id])
                    .select_from(agus)
                    .where(
                        (agus.c.group_id == quota_scope.scope_id) & (agus.c.user_id == user["uuid"])
                    )
                )
                matched_group_id = await conn.scalar(query)
                if matched_group_id:
                    return

    raise InvalidAPIParameters


class VirtualFolder(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    host = graphene.String()
    quota_scope_id = graphene.String()
    name = graphene.String()
    user = graphene.UUID()  # User.id (current owner, null in project vfolders)
    user_email = graphene.String()  # User.email (current owner, null in project vfolders)
    group = graphene.UUID()  # Group.id (current owner, null in user vfolders)
    group_name = graphene.String()  # Group.name (current owenr, null in user vfolders)
    creator = graphene.String()  # User.email (always set)
    unmanaged_path = graphene.String()
    usage_mode = graphene.String()
    permission = graphene.String()
    ownership_type = graphene.String()
    max_files = graphene.Int()
    max_size = BigInt()  # in MiB
    created_at = GQLDateTime()
    last_used = GQLDateTime()

    num_files = graphene.Int()
    cur_size = BigInt()
    # num_attached = graphene.Int()
    cloneable = graphene.Boolean()
    status = graphene.String()

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[VirtualFolder]:
        if row is None:
            return None

        return cls(
            id=row["id"],
            host=row["host"],
            quota_scope_id=row["quota_scope_id"],
            name=row["name"],
            user=row["user"],
            user_email=row["users_email"] if "users_email" in row else None,
            group=row["group"],
            group_name=row["groups_name"] if "groups_name" in row else None,
            creator=row["creator"],
            unmanaged_path=row["unmanaged_path"],
            usage_mode=row["usage_mode"],
            permission=row["permission"],
            ownership_type=row["ownership_type"],
            max_files=row["max_files"],
            max_size=row["max_size"],  # in MiB
            created_at=row["created_at"],
            last_used=row["last_used"],
            # num_attached=row['num_attached'],
            cloneable=row["cloneable"],
            status=row["status"],
            cur_size=row["cur_size"],
        )

    async def resolve_num_files(self, info: graphene.ResolveInfo) -> int:
        # TODO: measure on-the-fly
        return 0

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "id": ("vfolders_id", uuid.UUID),
        "host": ("vfolders_host", None),
        "quota_scope_id": ("vfolders_quota_scope_id", None),
        "name": ("vfolders_name", None),
        "group": ("vfolders_group", uuid.UUID),
        "group_name": ("groups_name", None),
        "user": ("vfolders_user", uuid.UUID),
        "user_email": ("users_email", None),
        "creator": ("vfolders_creator", None),
        "unmanaged_path": ("vfolders_unmanaged_path", None),
        "usage_mode": (
            "vfolders_usage_mode",
            enum_field_getter(VFolderUsageMode),
        ),
        "permission": (
            "vfolders_permission",
            enum_field_getter(VFolderPermission),
        ),
        "ownership_type": (
            "vfolders_ownership_type",
            enum_field_getter(VFolderOwnershipType),
        ),
        "max_files": ("vfolders_max_files", None),
        "max_size": ("vfolders_max_size", None),
        "created_at": ("vfolders_created_at", dtparse),
        "last_used": ("vfolders_last_used", dtparse),
        "cloneable": ("vfolders_cloneable", None),
        "status": (
            "vfolders_status",
            enum_field_getter(VFolderOperationStatus),
        ),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("vfolders_id", None),
        "host": ("vfolders_host", None),
        "quota_scope_id": ("vfolders_quota_scope_id", None),
        "name": ("vfolders_name", None),
        "group": ("vfolders_group", None),
        "group_name": ("groups_name", None),
        "user": ("vfolders_user", None),
        "user_email": ("users_email", None),
        "creator": ("vfolders_creator", None),
        "usage_mode": ("vfolders_usage_mode", None),
        "permission": ("vfolders_permission", None),
        "ownership_type": ("vfolders_ownership_type", None),
        "max_files": ("vfolders_max_files", None),
        "max_size": ("vfolders_max_size", None),
        "created_at": ("vfolders_created_at", None),
        "last_used": ("vfolders_last_used", None),
        "cloneable": ("vfolders_cloneable", None),
        "status": ("vfolders_status", None),
        "cur_size": ("vfolders_cur_size", None),
    }

    @classmethod
    async def load_count(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        user_id: uuid.UUID = None,
        filter: str = None,
    ) -> int:
        from .user import users

        j = vfolders.join(users, vfolders.c.user == users.c.uuid, isouter=True)
        query = sa.select([sa.func.count()]).select_from(j)
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(vfolders.c.group == group_id)
        if user_id is not None:
            query = query.where(vfolders.c.user == user_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        user_id: uuid.UUID = None,
        filter: str = None,
        order: str = None,
    ) -> Sequence[VirtualFolder]:
        from .group import groups
        from .user import users

        j = vfolders.join(users, vfolders.c.user == users.c.uuid, isouter=True).join(
            groups, vfolders.c.group == groups.c.id, isouter=True
        )
        query = (
            sa.select([vfolders, users.c.email, groups.c.name.label("groups_name")])
            .select_from(j)
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(vfolders.c.group == group_id)
        if user_id is not None:
            query = query.where(vfolders.c.user == user_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(vfolders.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, r)) is not None
            ]

    @classmethod
    async def batch_load_by_id(
        cls,
        graph_ctx: GraphQueryContext,
        ids: list[str],
        *,
        domain_name: str | None = None,
        group_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        filter: str | None = None,
    ) -> Sequence[Sequence[VirtualFolder]]:
        from .user import UserRow

        j = sa.join(VFolderRow, UserRow, VFolderRow.user == UserRow.uuid)
        query = (
            sa.select(VFolderRow)
            .select_from(j)
            .where(VFolderRow.id.in_(ids))
            .order_by(sa.desc(VFolderRow.created_at))
        )
        if user_id is not None:
            query = query.where(VFolderRow.user == user_id)
            if domain_name is not None:
                query = query.where(UserRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(VFolderRow.group == group_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly_session() as db_sess:
            return await batch_multiresult(
                graph_ctx,
                db_sess,
                query,
                cls,
                ids,
                lambda row: row["user"],
            )

    @classmethod
    async def batch_load_by_user(
        cls,
        graph_ctx: GraphQueryContext,
        user_uuids: Sequence[uuid.UUID],
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
    ) -> Sequence[Sequence[VirtualFolder]]:
        from .user import users

        # TODO: num_attached count group-by
        j = sa.join(vfolders, users, vfolders.c.user == users.c.uuid)
        query = (
            sa.select([vfolders])
            .select_from(j)
            .where(vfolders.c.user.in_(user_uuids))
            .order_by(sa.desc(vfolders.c.created_at))
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(vfolders.c.group == group_id)
        async with graph_ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                graph_ctx,
                conn,
                query,
                cls,
                user_uuids,
                lambda row: row["user"],
            )

    @classmethod
    async def load_count_invited(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        user_id: uuid.UUID = None,
        filter: str = None,
    ) -> int:
        from .user import users

        j = vfolders.join(
            vfolder_permissions,
            vfolders.c.id == vfolder_permissions.c.vfolder,
        ).join(
            users,
            vfolder_permissions.c.user == users.c.uuid,
        )
        query = (
            sa.select([sa.func.count()])
            .select_from(j)
            .where(
                (vfolder_permissions.c.user == user_id)
                & (vfolders.c.ownership_type == VFolderOwnershipType.USER),
            )
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice_invited(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        user_id: uuid.UUID = None,
        filter: str = None,
        order: str = None,
    ) -> list[VirtualFolder]:
        from .user import users

        j = vfolders.join(
            vfolder_permissions,
            vfolders.c.id == vfolder_permissions.c.vfolder,
        ).join(
            users,
            vfolder_permissions.c.user == users.c.uuid,
        )
        query = (
            sa.select([vfolders, users.c.email])
            .select_from(j)
            .where(
                (vfolder_permissions.c.user == user_id)
                & (vfolders.c.ownership_type == VFolderOwnershipType.USER),
            )
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(users.c.domain_name == domain_name)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(vfolders.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, r)) is not None
            ]

    @classmethod
    async def load_count_project(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        user_id: uuid.UUID = None,
        filter: str = None,
    ) -> int:
        from ai.backend.manager.models import association_groups_users as agus

        from .group import groups

        query = sa.select([agus.c.group_id]).select_from(agus).where(agus.c.user_id == user_id)

        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)

        grps = result.fetchall()
        group_ids = [g.group_id for g in grps]
        j = sa.join(vfolders, groups, vfolders.c.group == groups.c.id)
        query = sa.select([sa.func.count()]).select_from(j).where(vfolders.c.group.in_(group_ids))

        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice_project(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: str = None,
        group_id: uuid.UUID = None,
        user_id: uuid.UUID = None,
        filter: str = None,
        order: str = None,
    ) -> list[VirtualFolder]:
        from ai.backend.manager.models import association_groups_users as agus

        from .group import groups

        query = sa.select([agus.c.group_id]).select_from(agus).where(agus.c.user_id == user_id)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
        grps = result.fetchall()
        group_ids = [g.group_id for g in grps]
        j = vfolders.join(groups, vfolders.c.group == groups.c.id)
        query = (
            sa.select(
                [
                    vfolders,
                    groups.c.name.label("groups_name"),
                ]
            )
            .select_from(j)
            .where(vfolders.c.group.in_(group_ids))
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(groups.c.domain_name == domain_name)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(vfolders.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, r)) is not None
            ]


class VirtualFolderList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(VirtualFolder, required=True)


class VirtualFolderPermission(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    permission = graphene.String()
    vfolder = graphene.UUID()
    vfolder_name = graphene.String()
    user = graphene.UUID()
    user_email = graphene.String()

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[VirtualFolderPermission]:
        if row is None:
            return None
        return cls(
            permission=row["permission"],
            vfolder=row["vfolder"],
            vfolder_name=row["name"],
            user=row["user"],
            user_email=row["email"],
        )

    _queryfilter_fieldspec: Mapping[str, FieldSpecItem] = {
        "permission": ("vfolder_permissions_permission", enum_field_getter(VFolderPermission)),
        "vfolder": ("vfolder_permissions_vfolder", None),
        "vfolder_name": ("vfolders_name", None),
        "user": ("vfolder_permissions_user", None),
        "user_email": ("users_email", None),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "permission": ("vfolder_permissions_permission", None),
        "vfolder": ("vfolder_permissions_vfolder", None),
        "vfolder_name": ("vfolders_name", None),
        "user": ("vfolder_permissions_user", None),
        "user_email": ("users_email", None),
    }

    @classmethod
    async def load_count(
        cls,
        graph_ctx: GraphQueryContext,
        *,
        user_id: uuid.UUID = None,
        filter: str = None,
    ) -> int:
        from .user import users

        j = vfolder_permissions.join(vfolders, vfolders.c.id == vfolder_permissions.c.vfolder).join(
            users, users.c.uuid == vfolder_permissions.c.user
        )
        query = sa.select([sa.func.count()]).select_from(j)
        if user_id is not None:
            query = query.where(vfolders.c.user == user_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with graph_ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        graph_ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        user_id: uuid.UUID = None,
        filter: str = None,
        order: str = None,
    ) -> list[VirtualFolderPermission]:
        from .user import users

        j = vfolder_permissions.join(vfolders, vfolders.c.id == vfolder_permissions.c.vfolder).join(
            users, users.c.uuid == vfolder_permissions.c.user
        )
        query = (
            sa.select([vfolder_permissions, vfolders.c.name, users.c.email])
            .select_from(j)
            .limit(limit)
            .offset(offset)
        )
        if user_id is not None:
            query = query.where(vfolders.c.user == user_id)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(vfolders.c.created_at.desc())
        async with graph_ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(graph_ctx, r)) is not None
            ]


class VirtualFolderPermissionList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(VirtualFolderPermission, required=True)


class QuotaDetails(graphene.ObjectType):
    usage_bytes = BigInt(required=False)
    usage_count = BigInt(required=False)
    hard_limit_bytes = BigInt(required=False)


class QuotaScope(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    id = graphene.ID(required=True)
    quota_scope_id = graphene.String(required=True)
    storage_host_name = graphene.String(required=True)
    details = graphene.NonNull(QuotaDetails)

    @classmethod
    def from_vfolder_row(cls, ctx: GraphQueryContext, row: VFolderRow) -> QuotaScope:
        return QuotaScope(
            quota_scope_id=str(row.quota_scope_id),
            storage_host_name=row.host,
        )

    def resolve_id(self, info: graphene.ResolveInfo) -> str:
        return f"QuotaScope:{self.storage_host_name}/{self.quota_scope_id}"

    async def resolve_details(self, info: graphene.ResolveInfo) -> Optional[int]:
        from ai.backend.manager.models import GroupRow, UserRow

        graph_ctx: GraphQueryContext = info.context
        proxy_name, volume_name = graph_ctx.storage_manager.split_host(self.storage_host_name)
        try:
            async with graph_ctx.storage_manager.request(
                proxy_name,
                "GET",
                "quota-scope",
                json={"volume": volume_name, "qsid": self.quota_scope_id},
                raise_for_status=True,
            ) as (_, storage_resp):
                quota_config = await storage_resp.json()
                usage_bytes = quota_config["used_bytes"]
                if usage_bytes is not None and usage_bytes < 0:
                    usage_bytes = None
                return QuotaDetails(
                    # FIXME: limit scaning this only for fast scan capable volumes
                    usage_bytes=usage_bytes,
                    hard_limit_bytes=quota_config["limit_bytes"] or None,
                    usage_count=None,  # TODO: Implement
                )
        except aiohttp.ClientResponseError:
            qsid = QuotaScopeID.parse(self.quota_scope_id)
            async with graph_ctx.db.begin_readonly_session() as sess:
                await ensure_quota_scope_accessible_by_user(sess, qsid, graph_ctx.user)
                if qsid.scope_type == QuotaScopeType.USER:
                    query = (
                        sa.select(UserRow)
                        .where(UserRow.uuid == qsid.scope_id)
                        .options(selectinload(UserRow.resource_policy_row))
                    )
                else:
                    query = (
                        sa.select(GroupRow)
                        .where(GroupRow.id == qsid.scope_id)
                        .options(selectinload(GroupRow.resource_policy_row))
                    )
                result = await sess.scalar(query)
                resource_policy_constraint = result.resource_policy_row.max_vfolder_size
                if resource_policy_constraint is not None and resource_policy_constraint < 0:
                    resource_policy_constraint = None

            return QuotaDetails(
                usage_bytes=None,
                hard_limit_bytes=resource_policy_constraint,
                usage_count=None,  # TODO: Implement
            )


class QuotaScopeInput(graphene.InputObjectType):
    hard_limit_bytes = BigInt(required=False)


class SetQuotaScope(graphene.Mutation):
    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        quota_scope_id = graphene.String(required=True)
        storage_host_name = graphene.String(required=True)
        props = QuotaScopeInput(required=True)

    quota_scope = graphene.Field(lambda: QuotaScope)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        quota_scope_id: str,
        storage_host_name: str,
        props: QuotaScopeInput,
    ) -> SetQuotaScope:
        qsid = QuotaScopeID.parse(quota_scope_id)
        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_readonly_session() as sess:
            await ensure_quota_scope_accessible_by_user(sess, qsid, graph_ctx.user)

        max_vfolder_size = props.hard_limit_bytes
        proxy_name, volume_name = graph_ctx.storage_manager.split_host(storage_host_name)
        request_body = {
            "volume": volume_name,
            "qsid": str(qsid),
            "options": {"limit_bytes": max_vfolder_size},
        }
        async with graph_ctx.storage_manager.request(
            proxy_name,
            "PATCH",
            "quota-scope",
            json=request_body,
            raise_for_status=True,
        ):
            pass
        return cls(
            QuotaScope(
                quota_scope_id=quota_scope_id,
                storage_host_name=storage_host_name,
            )
        )


class UnsetQuotaScope(graphene.Mutation):
    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
    )

    class Arguments:
        quota_scope_id = graphene.String(required=True)
        storage_host_name = graphene.String(required=True)

    quota_scope = graphene.Field(lambda: QuotaScope)

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        quota_scope_id: str,
        storage_host_name: str,
    ) -> SetQuotaScope:
        qsid = QuotaScopeID.parse(quota_scope_id)
        graph_ctx: GraphQueryContext = info.context
        proxy_name, volume_name = graph_ctx.storage_manager.split_host(storage_host_name)
        request_body: dict[str, Any] = {
            "volume": volume_name,
            "qsid": str(qsid),
        }
        async with graph_ctx.db.begin_readonly_session() as sess:
            await ensure_quota_scope_accessible_by_user(sess, qsid, graph_ctx.user)
        async with graph_ctx.storage_manager.request(
            proxy_name,
            "DELETE",
            "quota-scope/quota",
            json=request_body,
            raise_for_status=True,
        ):
            pass

        return cls(
            QuotaScope(
                quota_scope_id=quota_scope_id,
                storage_host_name=storage_host_name,
            )
        )
