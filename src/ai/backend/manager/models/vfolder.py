from __future__ import annotations

import enum
import logging
import os.path
import uuid
from collections.abc import Container, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    List,
    NamedTuple,
    Optional,
    Sequence,
    TypeAlias,
    cast,
)

import aiohttp
import aiotools
import graphene
import sqlalchemy as sa
import trafaret as t
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only, relationship, selectinload

from ai.backend.common.bgtask import ProgressReporter
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    MountPermission,
    QuotaScopeID,
    QuotaScopeType,
    SessionId,
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)

from ..api.exceptions import (
    InvalidAPIParameters,
    ObjectNotFound,
    VFolderNotFound,
    VFolderOperationFailed,
    VFolderPermissionError,
)
from ..defs import (
    RESERVED_VFOLDER_PATTERNS,
    RESERVED_VFOLDERS,
    VFOLDER_DSTPATHS_MAP,
)
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
    StrEnumType,
    batch_multiresult,
    metadata,
)
from .group import GroupRow
from .minilang.ordering import OrderSpecItem, QueryOrderParser
from .minilang.queryfilter import FieldSpecItem, QueryFilterParser, enum_field_getter
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    BaseScope,
    DomainScope,
    ProjectScope,
    ScopedUserRole,
    StorageHost,
    get_roles_in_scope,
)
from .rbac import (
    UserScope as UserRBACScope,
)
from .rbac.context import ClientContext
from .rbac.exceptions import InvalidScope, NotEnoughPermission
from .rbac.permission_defs import StorageHostPermission
from .rbac.permission_defs import VFolderPermission as VFolderRBACPermission
from .session import DEAD_SESSION_STATUSES, SessionRow
from .storage import PermissionContext as StorageHostPermissionContext
from .storage import PermissionContextBuilder as StorageHostPermissionContextBuilder
from .user import UserRole, UserRow
from .utils import ExtendedAsyncSAEngine, execute_with_retry, sql_json_merge

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
    "VFolderStatusSet",
    "DEAD_VFOLDER_STATUSES",
    "VFolderCloneInfo",
    "VFolderDeletionInfo",
    "VFolderRow",
    "QuotaScope",
    "SetQuotaScope",
    "UnsetQuotaScope",
    "query_accessible_vfolders",
    "initiate_vfolder_clone",
    "initiate_vfolder_deletion",
    "get_allowed_vfolder_hosts_by_group",
    "get_allowed_vfolder_hosts_by_user",
    "verify_vfolder_name",
    "prepare_vfolder_mounts",
    "update_vfolder_status",
    "filter_host_allowed_permission",
    "ensure_host_permission_allowed",
    "vfolder_status_map",
    "DEAD_VFOLDER_STATUSES",
    "SOFT_DELETED_VFOLDER_STATUSES",
    "HARD_DELETED_VFOLDER_STATUSES",
    "VFolderPermissionSetAlias",
)


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class VFolderOwnershipType(enum.StrEnum):
    """
    Ownership type of virtual folder.
    """

    USER = "user"
    GROUP = "group"


class VFolderPermission(enum.StrEnum):
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


class VFolderInvitationState(enum.StrEnum):
    """
    Virtual Folder invitation state.
    """

    PENDING = "pending"
    CANCELED = "canceled"  # canceled by inviter
    ACCEPTED = "accepted"
    REJECTED = "rejected"  # rejected by invitee


class VFolderOperationStatus(enum.StrEnum):
    """
    Introduce virtual folder current status for storage-proxy operations.
    """

    READY = "ready"
    PERFORMING = "performing"
    CLONING = "cloning"
    MOUNTED = "mounted"
    ERROR = "error"

    DELETE_PENDING = "delete-pending"  # vfolder is in trash bin
    DELETE_ONGOING = "delete-ongoing"  # vfolder is being deleted in storage
    DELETE_COMPLETE = "delete-complete"  # vfolder is deleted permanently, only DB row remains
    DELETE_ERROR = "delete-error"


class VFolderStatusSet(enum.StrEnum):
    """
    Acts as an alias to represent set of VFolder statuses. Use this value as a key of
    `vfolder_status_map` dictionary to retrieve actual `VFolderOperationStatus` values.
    """

    READABLE = "readable"
    """Represents VFolder in a normal (readable, mountable and clonable) state"""

    MOUNTABLE = "mountable"
    """Represents VFolder in a mountable state"""

    UPDATABLE = "updatable"
    """Represents VFolder in idle (not performing active clone or removal) state"""

    DELETABLE = "deletable"
    """Simillar with UPDATABLE but does not allow VFolder in MOUNTED state"""

    PURGABLE = "purgable"
    """Represents VFolder located in trash bin. The meaning of `purge` here is
    completely different between our VFolder `/purge` API so be sure not to confuse.
    That API will be renamed any soon in a more self-representitive way."""

    RECOVERABLE = "recoverable"
    """alias of VFolderStatusSet.PURGABLE"""

    INACCESSIBLE = "inaccessible"
    """Represents VFolder which is now completely removed from storage and only its record is being kept"""


vfolder_status_map: Final[dict[VFolderStatusSet, set[VFolderOperationStatus]]] = {
    VFolderStatusSet.READABLE: {
        VFolderOperationStatus.READY,
        VFolderOperationStatus.PERFORMING,
        VFolderOperationStatus.CLONING,
        VFolderOperationStatus.MOUNTED,
        VFolderOperationStatus.ERROR,
        VFolderOperationStatus.DELETE_PENDING,
    },
    VFolderStatusSet.MOUNTABLE: {
        VFolderOperationStatus.READY,
        VFolderOperationStatus.PERFORMING,
        VFolderOperationStatus.CLONING,
        VFolderOperationStatus.MOUNTED,
    },
    # if UPDATABLE access status is requested, READY and MOUNTED operation statuses are accepted.
    VFolderStatusSet.UPDATABLE: {
        VFolderOperationStatus.READY,
        VFolderOperationStatus.MOUNTED,
    },
    # if DELETABLE access status is requested, only READY operation status is accepted.
    VFolderStatusSet.DELETABLE: {
        VFolderOperationStatus.READY,
    },
    # if DELETABLE access status is requested, DELETE_PENDING, DELETE_COMPLETE operation status is accepted.
    VFolderStatusSet.PURGABLE: {
        VFolderOperationStatus.DELETE_PENDING,
        VFolderOperationStatus.DELETE_COMPLETE,
    },
    VFolderStatusSet.RECOVERABLE: {
        VFolderOperationStatus.DELETE_PENDING,
    },
    VFolderStatusSet.INACCESSIBLE: {
        VFolderOperationStatus.DELETE_COMPLETE,
    },
}


class VFolderPermissionSetAlias(enum.Enum):
    READABLE = {
        VFolderPermission.READ_ONLY,
        VFolderPermission.READ_WRITE,
        VFolderPermission.RW_DELETE,
    }
    WRITABLE = {VFolderPermission.READ_WRITE, VFolderPermission.RW_DELETE}
    DELETABLE = {VFolderPermission.RW_DELETE}


SOFT_DELETED_VFOLDER_STATUSES = (
    VFolderOperationStatus.DELETE_PENDING,
    VFolderOperationStatus.DELETE_ONGOING,
)

HARD_DELETED_VFOLDER_STATUSES = (
    VFolderOperationStatus.DELETE_COMPLETE,
    VFolderOperationStatus.DELETE_ERROR,
)

DEAD_VFOLDER_STATUSES = (
    *SOFT_DELETED_VFOLDER_STATUSES,
    *HARD_DELETED_VFOLDER_STATUSES,
)


class VFolderDeletionInfo(NamedTuple):
    vfolder_id: VFolderID
    host: str


class VFolderCloneInfo(NamedTuple):
    source_vfolder_id: VFolderID
    source_host: str
    domain_name: str

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
    sa.Column("host", sa.String(length=128), nullable=False, index=True),
    sa.Column("domain_name", sa.String(length=64), nullable=False, index=True),
    sa.Column("quota_scope_id", QuotaScopeIDType, nullable=False),
    sa.Column("name", sa.String(length=64), nullable=False, index=True),
    sa.Column(
        "usage_mode",
        EnumValueType(VFolderUsageMode),
        default=VFolderUsageMode.GENERAL,
        nullable=False,
        index=True,
    ),
    sa.Column(
        "permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE
    ),  # legacy
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
        index=True,
    ),
    sa.Column("user", GUID, nullable=True),  # owner if user vfolder
    sa.Column("group", GUID, nullable=True),  # owner if project vfolder
    sa.Column("cloneable", sa.Boolean, default=False, nullable=False),
    sa.Column(
        "status",
        StrEnumType(VFolderOperationStatus),
        default=VFolderOperationStatus.READY,
        server_default=VFolderOperationStatus.READY,
        nullable=False,
        index=True,
    ),
    # status_history records the most recent status changes for each status
    # e.g)
    # {
    #   "ready": "2022-10-22T10:22:30",
    #   "delete-pending": "2022-10-22T11:40:30",
    #   "delete-ongoing": "2022-10-25T10:22:30"
    # }
    sa.Column("status_history", pgsql.JSONB(), nullable=True, default=sa.null()),
    sa.Column("status_changed", sa.DateTime(timezone=True), nullable=True, index=True),
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
    IDColumn(),
    sa.Column("permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE),
    sa.Column(
        "vfolder",
        GUID,
        sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=False),
)


class VFolderPermissionRow(Base):
    __table__ = vfolder_permissions

    vfolder_row = relationship("VFolderRow", back_populates="permission_rows")


class VFolderRow(Base):
    __table__ = vfolders

    endpoints = relationship("EndpointRow", back_populates="model_row")
    user_row = relationship(
        "UserRow",
        back_populates="vfolder_rows",
        primaryjoin="UserRow.uuid == foreign(VFolderRow.user)",
    )
    group_row = relationship(
        "GroupRow",
        back_populates="vfolder_rows",
        primaryjoin="GroupRow.id == foreign(VFolderRow.group)",
    )
    permission_rows = relationship(VFolderPermissionRow, back_populates="vfolder_row")

    @classmethod
    async def get(
        cls,
        session: SASession,
        id: uuid.UUID,
        load_user: bool = False,
        load_group: bool = False,
    ) -> VFolderRow:
        query = sa.select(VFolderRow).where(VFolderRow.id == id)
        if load_user:
            query = query.options(selectinload(VFolderRow.user_row))
        if load_group:
            query = query.options(selectinload(VFolderRow.group_row))

        result = await session.scalar(query)
        if not result:
            raise ObjectNotFound(object_name="VFolder")
        return result

    def __contains__(self, key):
        return key in self.__dir__()

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    @property
    def vfid(self) -> VFolderID:
        return VFolderID(self.quota_scope_id, self.id)


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
    allowed_status_set: VFolderStatusSet | None = None,
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
            entries.append({
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
            })

    entries: List[dict] = []
    # User vfolders.
    if "user" in allowed_vfolder_types:
        # Scan vfolders on requester's behalf.
        j = vfolders.join(users, vfolders.c.user == users.c.uuid)
        query = sa.select(
            vfolders_selectors + [vfolders.c.permission, users.c.email], use_labels=True
        ).select_from(j)
        if allowed_status_set is not None:
            query = query.where(vfolders.c.status.in_(vfolder_status_map[allowed_status_set]))
        else:
            query = query.where(
                vfolders.c.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE])
            )
        if not allow_privileged_access or (
            user_role != UserRole.ADMIN and user_role != UserRole.SUPERADMIN
        ):
            query = query.where(vfolders.c.user == user_uuid)
        await _append_entries(query)

        # Scan vfolders shared with requester.
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
                & (vfolders.c.ownership_type == VFolderOwnershipType.USER)
            )
        )
        if allowed_status_set is not None:
            query = query.where(vfolders.c.status.in_(vfolder_status_map[allowed_status_set]))
        else:
            query = query.where(
                vfolders.c.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE])
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
            .where((vfolders.c.group.in_(group_ids)) & (vfolder_permissions.c.user == user_uuid))
        )
        if allowed_status_set is not None:
            query = query.where(vfolders.c.status.in_(vfolder_status_map[allowed_status_set]))
        else:
            query = query.where(
                vfolders.c.status.not_in(vfolder_status_map[VFolderStatusSet.INACCESSIBLE])
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
    requested_mount_reference_options: Mapping[str | uuid.UUID, Any],
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
    requested_mount_options: dict[str, dict[str, Any]] = {
        name: options
        for name, options in requested_mount_reference_options.items()
        if isinstance(name, str)
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
        if options := requested_mount_reference_options.get(vfid):
            requested_mount_options[name] = options

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
    extra_vf_conds = vfolders.c.name.startswith(".") & vfolders.c.status.not_in(
        DEAD_VFOLDER_STATUSES
    )
    if requested_vfolder_names:
        extra_vf_conds = extra_vf_conds | (
            vfolders.c.name.in_(requested_vfolder_names.values())
            & vfolders.c.status.not_in(DEAD_VFOLDER_STATUSES)
        )
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
                    "relpaths": [str(user_scope.user_uuid.hex)],
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
            match requested_perm := requested_mount_options.get(key, {}).get("permission"):
                case MountPermission.READ_ONLY:
                    mount_perm = MountPermission.READ_ONLY
                case MountPermission.READ_WRITE | MountPermission.RW_DELETE:
                    if vfolder["permission"] == VFolderPermission.READ_ONLY:
                        raise VFolderPermissionError(
                            f"VFolder {vfolder_name} is allowed to be accessed in '{vfolder['permission'].value}' mode, "
                            f"but attempted with '{requested_perm.value}' mode."
                        )
                    mount_perm = requested_perm
                case _:  # None if unset
                    mount_perm = vfolder["permission"]
            matched_vfolder_mounts.append(
                VFolderMount(
                    name=vfolder["name"],
                    vfid=VFolderID(vfolder["quota_scope_id"], vfolder["id"]),
                    vfsubpath=PurePosixPath(requested_vfolder_subpaths[key]),
                    host_path=mount_base_path / requested_vfolder_subpaths[key],
                    kernel_path=kernel_path,
                    mount_perm=mount_perm,
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


async def update_vfolder_status(
    engine: ExtendedAsyncSAEngine,
    vfolder_ids: Sequence[uuid.UUID],
    update_status: VFolderOperationStatus,
    do_log: bool = True,
) -> None:
    vfolder_info_len = len(vfolder_ids)
    cond = vfolders.c.id.in_(vfolder_ids)
    if vfolder_info_len == 0:
        return None
    elif vfolder_info_len == 1:
        cond = vfolders.c.id == vfolder_ids[0]

    now = datetime.now(tzutc())

    if update_status == VFolderOperationStatus.DELETE_PENDING:
        select_stmt = sa.select(VFolderRow).where(VFolderRow.id.in_(vfolder_ids))
        async with engine.begin_readonly_session() as db_session:
            for vf_row in await db_session.scalars(select_stmt):
                vf_row = cast(VFolderRow, vf_row)
                mount_sessions = await get_sessions_by_mounted_folder(
                    db_session, VFolderID.from_row(vf_row)
                )
                if mount_sessions:
                    session_ids = [str(s) for s in mount_sessions]
                    raise InvalidAPIParameters(
                        f"Cannot delete the vfolder. The vfolder(id: {vf_row.id}) is mounted on sessions(ids: {session_ids})"
                    )

    async def _update() -> None:
        async with engine.begin_session() as db_session:
            query = (
                sa.update(vfolders)
                .values(
                    status=update_status,
                    status_changed=now,
                    status_history=sql_json_merge(
                        vfolders.c.status_history,
                        (),
                        {
                            update_status.name: now.isoformat(),
                        },
                    ),
                )
                .where(cond)
            )
            await db_session.execute(query)

    await execute_with_retry(_update)
    if do_log:
        log.debug(
            "Successfully updated status of VFolder(s) {} to {}",
            [str(x) for x in vfolder_ids],
            update_status.name,
        )


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
                    "domain_name": vfolder_info.domain_name,
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


async def initiate_vfolder_deletion(
    db_engine: ExtendedAsyncSAEngine,
    requested_vfolders: Sequence[VFolderDeletionInfo],
    storage_manager: StorageSessionManager,
    storage_ptask_group: aiotools.PersistentTaskGroup,
) -> int:
    """Purges VFolder content from storage host."""
    vfolder_info_len = len(requested_vfolders)
    vfolder_ids = tuple(vf_id.folder_id for vf_id, _ in requested_vfolders)
    vfolders.c.id.in_(vfolder_ids)
    if vfolder_info_len == 0:
        return 0
    elif vfolder_info_len == 1:
        vfolders.c.id == vfolder_ids[0]
    await update_vfolder_status(
        db_engine, vfolder_ids, VFolderOperationStatus.DELETE_ONGOING, do_log=False
    )

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

            await update_vfolder_status(
                db_engine, vfolder_ids, VFolderOperationStatus.DELETE_COMPLETE, do_log=False
            )
            log.debug("Successfully removed vfolders {}", [str(x) for x in vfolder_ids])
        if failed_deletion:
            await update_vfolder_status(
                db_engine,
                [vfid.vfolder_id for vfid, _ in failed_deletion],
                VFolderOperationStatus.DELETE_ERROR,
                do_log=False,
            )
            extra_data = {str(vfid.vfolder_id): err_msg for vfid, err_msg in failed_deletion}
            raise VFolderOperationFailed(extra_data=extra_data)

    storage_ptask_group.create_task(_delete(), name="delete_vfolders")
    log.debug("Started purging vfolders {}", [str(x) for x in vfolder_ids])

    return vfolder_info_len


async def ensure_quota_scope_accessible_by_user(
    conn: SASession,
    quota_scope: QuotaScopeID,
    user: Mapping[str, Any],
) -> None:
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


async def get_sessions_by_mounted_folder(
    db_session: SASession, vfolder_id: VFolderID
) -> tuple[SessionId]:
    """
    Return a tuple of sessions.id that the give folder is mounted on.
    """

    select_stmt = (
        sa.select(SessionRow)
        .where(
            (SessionRow.status.not_in(DEAD_SESSION_STATUSES))
            & SessionRow.vfolder_mounts.contains([{"vfid": str(vfolder_id)}])
        )
        .options(load_only(SessionRow.id))
    )

    session_rows = (await db_session.scalars(select_stmt)).all()
    return tuple([session.id for session in session_rows])


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
    domain_name = graphene.String(description="Added in 24.09.0.")
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
    def from_row(cls, ctx: GraphQueryContext, row: Row | VFolderRow) -> Optional[VirtualFolder]:
        if row is None:
            return None

        def _get_field(name: str) -> Any:
            try:
                return row[name]
            except sa.exc.NoSuchColumnError:
                return None

        return cls(
            id=row["id"],
            host=row["host"],
            quota_scope_id=row["quota_scope_id"],
            name=row["name"],
            user=row["user"],
            user_email=_get_field("users_email"),
            group=row["group"],
            group_name=_get_field("groups_name"),
            creator=row["creator"],
            domain_name=row["domain_name"],
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

    @classmethod
    def from_orm_row(cls, row: VFolderRow) -> VirtualFolder:
        return cls(
            id=row.id,
            host=row.host,
            quota_scope_id=row.quota_scope_id,
            name=row.name,
            user=row.user,
            user_email=row.user_row.email if row.user_row is not None else None,
            group=row.group,
            group_name=row.group_row.name if row.group_row is not None else None,
            creator=row.creator,
            unmanaged_path=row.unmanaged_path,
            usage_mode=row.usage_mode,
            permission=row.permission,
            ownership_type=row.ownership_type,
            max_files=row.max_files,
            max_size=row.max_size,
            created_at=row.created_at,
            last_used=row.last_used,
            cloneable=row.cloneable,
            status=row.status,
            cur_size=row.cur_size,
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
        "domain_name": ("vfolders_domain_name", None),
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
            lambda s: VFolderOperationStatus(s),
        ),
    }

    _queryorder_colmap: Mapping[str, OrderSpecItem] = {
        "id": ("vfolders_id", None),
        "host": ("vfolders_host", None),
        "quota_scope_id": ("vfolders_quota_scope_id", None),
        "name": ("vfolders_name", None),
        "group": ("vfolders_group", None),
        "group_name": ("groups_name", None),
        "domain_name": ("domain_name", None),
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
        from .group import groups
        from .user import users

        j = vfolders.join(users, vfolders.c.user == users.c.uuid, isouter=True).join(
            groups, vfolders.c.group == groups.c.id, isouter=True
        )
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
            sa.select([
                vfolders,
                groups.c.name.label("groups_name"),
            ])
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
                resource_policy_constraint = result.resource_policy_row.max_quota_scope_size
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
        if props.hard_limit_bytes is Undefined:
            # Do nothing but just return the quota scope object.
            return cls(
                QuotaScope(
                    quota_scope_id=quota_scope_id,
                    storage_host_name=storage_host_name,
                )
            )
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


# RBAC
WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)
# TypeAlias is deprecated since 3.12 but mypy does not follow up yet

OWNER_PERMISSIONS: frozenset[VFolderRBACPermission] = frozenset([
    perm for perm in VFolderRBACPermission
])
ADMIN_PERMISSIONS: frozenset[VFolderRBACPermission] = frozenset([
    VFolderRBACPermission.READ_ATTRIBUTE,
    VFolderRBACPermission.UPDATE_ATTRIBUTE,
    VFolderRBACPermission.DELETE_VFOLDER,
])
MONITOR_PERMISSIONS: frozenset[VFolderRBACPermission] = frozenset([
    VFolderRBACPermission.READ_ATTRIBUTE,
    VFolderRBACPermission.UPDATE_ATTRIBUTE,
])
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[VFolderRBACPermission] = frozenset([
    VFolderRBACPermission.READ_ATTRIBUTE,
    VFolderRBACPermission.READ_CONTENT,
    VFolderRBACPermission.WRITE_CONTENT,
    VFolderRBACPermission.DELETE_CONTENT,
    VFolderRBACPermission.MOUNT_RO,
    VFolderRBACPermission.MOUNT_RW,
    VFolderRBACPermission.MOUNT_WD,
])
MEMBER_PERMISSIONS: frozenset[VFolderRBACPermission] = frozenset()

# TODO: Change type of `vfolder_permissions.permission` to VFolderRBACPermission
LEGACY_PERMISSION_TO_RBAC_PERMISSION_MAP: Mapping[
    VFolderPermission, frozenset[VFolderRBACPermission]
] = {
    VFolderPermission.READ_ONLY: frozenset([
        VFolderRBACPermission.READ_ATTRIBUTE,
        VFolderRBACPermission.READ_CONTENT,
    ]),
    VFolderPermission.READ_WRITE: frozenset([
        VFolderRBACPermission.READ_ATTRIBUTE,
        VFolderRBACPermission.UPDATE_ATTRIBUTE,
        VFolderRBACPermission.DELETE_VFOLDER,
        VFolderRBACPermission.READ_CONTENT,
        VFolderRBACPermission.WRITE_CONTENT,
        VFolderRBACPermission.DELETE_CONTENT,
        VFolderRBACPermission.MOUNT_RO,
        VFolderRBACPermission.MOUNT_RW,
    ]),
    VFolderPermission.RW_DELETE: frozenset([
        VFolderRBACPermission.READ_ATTRIBUTE,
        VFolderRBACPermission.UPDATE_ATTRIBUTE,
        VFolderRBACPermission.DELETE_VFOLDER,
        VFolderRBACPermission.READ_CONTENT,
        VFolderRBACPermission.WRITE_CONTENT,
        VFolderRBACPermission.DELETE_CONTENT,
        VFolderRBACPermission.MOUNT_RO,
        VFolderRBACPermission.MOUNT_RW,
        VFolderRBACPermission.MOUNT_WD,
    ]),
    VFolderPermission.OWNER_PERM: frozenset(OWNER_PERMISSIONS),
}

_VFOLDER_PERMISSION_TO_STORAGE_HOST_PERMISSION_MAP: Mapping[
    VFolderRBACPermission, StorageHostPermission
] = {
    VFolderRBACPermission.CLONE: StorageHostPermission.CLONE,
    VFolderRBACPermission.ASSIGN_PERMISSION_TO_OTHERS: StorageHostPermission.ASSIGN_PERMISSION_TO_OTHERS,
    VFolderRBACPermission.READ_ATTRIBUTE: StorageHostPermission.READ_ATTRIBUTE,
    VFolderRBACPermission.UPDATE_ATTRIBUTE: StorageHostPermission.UPDATE_ATTRIBUTE,
    VFolderRBACPermission.DELETE_VFOLDER: StorageHostPermission.DELETE_VFOLDER,
    VFolderRBACPermission.READ_CONTENT: StorageHostPermission.READ_CONTENT,
    VFolderRBACPermission.WRITE_CONTENT: StorageHostPermission.WRITE_CONTENT,
    VFolderRBACPermission.DELETE_CONTENT: StorageHostPermission.DELETE_CONTENT,
    VFolderRBACPermission.MOUNT_RO: StorageHostPermission.MOUNT_RO,
    VFolderRBACPermission.MOUNT_RW: StorageHostPermission.MOUNT_RW,
    VFolderRBACPermission.MOUNT_WD: StorageHostPermission.MOUNT_WD,
}

_STORAGE_HOST_PERMISSION_TO_VFOLDER_PERMISSION_MAP: Mapping[
    StorageHostPermission, VFolderRBACPermission
] = {
    StorageHostPermission.CLONE: VFolderRBACPermission.CLONE,
    StorageHostPermission.ASSIGN_PERMISSION_TO_OTHERS: VFolderRBACPermission.ASSIGN_PERMISSION_TO_OTHERS,
    StorageHostPermission.READ_ATTRIBUTE: VFolderRBACPermission.READ_ATTRIBUTE,
    StorageHostPermission.UPDATE_ATTRIBUTE: VFolderRBACPermission.UPDATE_ATTRIBUTE,
    StorageHostPermission.DELETE_VFOLDER: VFolderRBACPermission.DELETE_VFOLDER,
    StorageHostPermission.READ_CONTENT: VFolderRBACPermission.READ_CONTENT,
    StorageHostPermission.WRITE_CONTENT: VFolderRBACPermission.WRITE_CONTENT,
    StorageHostPermission.DELETE_CONTENT: VFolderRBACPermission.DELETE_CONTENT,
    StorageHostPermission.MOUNT_RO: VFolderRBACPermission.MOUNT_RO,
    StorageHostPermission.MOUNT_RW: VFolderRBACPermission.MOUNT_RW,
    StorageHostPermission.MOUNT_WD: VFolderRBACPermission.MOUNT_WD,
}


# RBAC
@dataclass
class VFolderPermissionContext(
    AbstractPermissionContext[VFolderRBACPermission, VFolderRow, uuid.UUID]
):
    host_permission_ctx: StorageHostPermissionContext | None = None

    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.user_id_to_permission_map:
            cond = _OR_coalesce(cond, VFolderRow.user.in_(self.user_id_to_permission_map.keys()))
        if self.project_id_to_permission_map:
            cond = _OR_coalesce(
                cond, VFolderRow.group.in_(self.project_id_to_permission_map.keys())
            )
        if self.domain_name_to_permission_map:
            cond = _OR_coalesce(
                cond, VFolderRow.domain_name.in_(self.domain_name_to_permission_map.keys())
            )
        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, VFolderRow.id.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, VFolderRow.id.in_(self.object_id_to_overriding_permission_map.keys())
            )

        if self.host_permission_ctx is not None:
            if cond is not None:
                host_names = self.host_permission_ctx.host_to_permissions_map.keys()
                cond = cond & VFolderRow.host.in_(host_names)
        return cond

    def apply_host_permission_ctx(self, host_permission_ctx: StorageHostPermissionContext) -> None:
        self.host_permission_ctx = host_permission_ctx

    async def build_query(self) -> sa.sql.Select | None:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(VFolderRow).where(cond)

    async def calculate_final_permission(
        self, rbac_obj: VFolderRow
    ) -> frozenset[VFolderRBACPermission]:
        vfolder_row = rbac_obj
        vfolder_id = cast(uuid.UUID, vfolder_row.id)
        permissions: set[VFolderRBACPermission] = set()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(vfolder_id)
        ) is not None:
            permissions = set(overriding_perm)
        else:
            permissions |= self.object_id_to_additional_permission_map.get(vfolder_id, set())
            permissions |= self.user_id_to_permission_map.get(vfolder_row.user, set())
            permissions |= self.project_id_to_permission_map.get(vfolder_row.group, set())
            permissions |= self.domain_name_to_permission_map.get(vfolder_row.domain_name, set())

        if self.host_permission_ctx is not None:
            host_permission_map = self.host_permission_ctx.host_to_permissions_map
            host_perms = host_permission_map.get(vfolder_row.host)
            if host_perms is not None:
                permissions &= {
                    _STORAGE_HOST_PERMISSION_TO_VFOLDER_PERMISSION_MAP[perm]
                    for perm in host_perms
                    if perm in _STORAGE_HOST_PERMISSION_TO_VFOLDER_PERMISSION_MAP
                }

        return frozenset(permissions)


class VFolderPermissionContextBuilder(
    AbstractPermissionContextBuilder[VFolderRBACPermission, VFolderPermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    async def build(
        self,
        ctx: ClientContext,
        target_scope: BaseScope,
        requested_permission: VFolderRBACPermission,
    ) -> VFolderPermissionContext:
        match target_scope:
            case DomainScope(domain_name):
                permission_ctx = await self.build_in_domain_scope(ctx, domain_name)
            case ProjectScope(project_id, domain_name):
                permission_ctx = await self.build_in_project_scope(ctx, project_id)
            case UserRBACScope(user_id, _):
                permission_ctx = await self.build_in_user_scope(ctx, user_id)
            case _:
                raise InvalidScope
        permission_ctx.filter_by_permission(requested_permission)
        return permission_ctx

    async def build_in_nested_scope(
        self,
        ctx: ClientContext,
        target_scope: BaseScope,
        requested_permission: VFolderRBACPermission,
    ) -> VFolderPermissionContext:
        match target_scope:
            case DomainScope(domain_name):
                permission_ctx = await self.build_in_domain_scope(ctx, domain_name)
                _user_perm_ctx = await self.build_in_user_scope_in_domain(
                    ctx, ctx.user_id, domain_name
                )
                permission_ctx = VFolderPermissionContext.merge(permission_ctx, _user_perm_ctx)
                _project_perm_ctx = await self.build_in_project_scopes_in_domain(ctx, domain_name)
                permission_ctx = VFolderPermissionContext.merge(permission_ctx, _project_perm_ctx)
            case ProjectScope(project_id, _):
                permission_ctx = await self.build_in_project_scope(ctx, project_id)
                _user_perm_ctx = await self.build_in_user_scope(ctx, ctx.user_id)
                permission_ctx = VFolderPermissionContext.merge(permission_ctx, _user_perm_ctx)
            case UserRBACScope(user_id, _):
                permission_ctx = await self.build_in_user_scope(ctx, user_id)
            case _:
                raise InvalidScope
        permission_ctx.filter_by_permission(requested_permission)
        return permission_ctx

    async def build_in_domain_scope(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> VFolderPermissionContext:
        roles = await get_roles_in_scope(ctx, DomainScope(domain_name), self.db_session)
        domain_permissions = await VFolderPermissionContextBuilder.calculate_permission_by_roles(
            roles
        )
        result = VFolderPermissionContext(
            domain_name_to_permission_map={domain_name: domain_permissions}
        )
        return result

    async def build_in_project_scopes_in_domain(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> VFolderPermissionContext:
        result = VFolderPermissionContext()

        _project_stmt = (
            sa.select(GroupRow)
            .where(GroupRow.domain_name == domain_name)
            .options(load_only(GroupRow.id))
        )
        for row in await self.db_session.scalars(_project_stmt):
            _row = cast(GroupRow, row)
            _project_perm_ctx = await self.build_in_project_scope(ctx, _row.id)
            result = VFolderPermissionContext.merge(result, _project_perm_ctx)
        return result

    async def build_in_user_scope_in_domain(
        self,
        ctx: ClientContext,
        user_id: uuid.UUID,
        domain_name: str,
    ) -> VFolderPermissionContext:
        # For Superadmin and monitor who can create vfolders in multiple different domains.
        roles = await get_roles_in_scope(ctx, UserRBACScope(user_id, domain_name), self.db_session)
        permissions = await VFolderPermissionContextBuilder.calculate_permission_by_roles(roles)

        _vfolder_stmt = (
            sa.select(VFolderRow)
            .where((VFolderRow.user == user_id) & (VFolderRow.domain_name == domain_name))
            .options(load_only(VFolderRow.id))
        )
        own_folder_map = {
            row.id: permissions for row in await self.db_session.scalars(_vfolder_stmt)
        }
        result = VFolderPermissionContext(object_id_to_additional_permission_map=own_folder_map)

        _stmt = (
            sa.select(VFolderPermissionRow)
            .select_from(sa.join(VFolderPermissionRow, VFolderRow))
            .where(
                (VFolderPermissionRow.user == ctx.user_id)
                & (
                    VFolderRow.ownership_type == VFolderOwnershipType.USER
                )  # filter out user vfolders
                & (VFolderRow.domain_name == domain_name)
            )
        )
        object_id_to_permission_map = {
            row.vfolder: LEGACY_PERMISSION_TO_RBAC_PERMISSION_MAP[row.permission]
            for row in await self.db_session.scalars(_stmt)
        }
        if ctx.user_role in (UserRole.SUPERADMIN, UserRole.ADMIN):
            ctx_to_merge = VFolderPermissionContext(
                object_id_to_additional_permission_map=object_id_to_permission_map
            )
        else:
            ctx_to_merge = VFolderPermissionContext(
                object_id_to_overriding_permission_map=object_id_to_permission_map
            )
        result = VFolderPermissionContext.merge(result, ctx_to_merge)
        return result

    async def build_in_project_scope(
        self,
        ctx: ClientContext,
        project_id: uuid.UUID,
    ) -> VFolderPermissionContext:
        roles = await get_roles_in_scope(ctx, ProjectScope(project_id), self.db_session)
        permissions = await VFolderPermissionContextBuilder.calculate_permission_by_roles(roles)
        result = VFolderPermissionContext(project_id_to_permission_map={project_id: permissions})

        _stmt = (
            sa.select(VFolderPermissionRow)
            .select_from(sa.join(VFolderPermissionRow, VFolderRow))
            .where(
                (VFolderPermissionRow.user == ctx.user_id)
                & (
                    VFolderRow.ownership_type == VFolderOwnershipType.GROUP
                )  # filter out user vfolders
            )
        )
        object_id_to_permission_map = {
            row.vfolder: LEGACY_PERMISSION_TO_RBAC_PERMISSION_MAP[row.permission]
            for row in await self.db_session.scalars(_stmt)
        }
        if ScopedUserRole.ADMIN in roles:
            result.object_id_to_additional_permission_map = object_id_to_permission_map
        else:
            result.object_id_to_overriding_permission_map = object_id_to_permission_map
        return result

    async def build_in_user_scope(
        self,
        ctx: ClientContext,
        user_id: uuid.UUID,
    ) -> VFolderPermissionContext:
        roles = await get_roles_in_scope(ctx, UserRBACScope(user_id), self.db_session)
        permissions = await VFolderPermissionContextBuilder.calculate_permission_by_roles(roles)
        result = VFolderPermissionContext(user_id_to_permission_map={user_id: permissions})

        _stmt = (
            sa.select(VFolderPermissionRow)
            .select_from(sa.join(VFolderPermissionRow, VFolderRow))
            .where(
                (VFolderPermissionRow.user == ctx.user_id)
                & (
                    VFolderRow.ownership_type == VFolderOwnershipType.USER
                )  # filter out user vfolders
            )
        )
        object_id_to_permission_map = {
            row.vfolder: LEGACY_PERMISSION_TO_RBAC_PERMISSION_MAP[row.permission]
            for row in await self.db_session.scalars(_stmt)
        }
        if ctx.user_role in (UserRole.SUPERADMIN, UserRole.ADMIN):
            result.object_id_to_additional_permission_map = object_id_to_permission_map
        else:
            result.object_id_to_overriding_permission_map = object_id_to_permission_map
        return result

    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return OWNER_PERMISSIONS

    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return ADMIN_PERMISSIONS

    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return MONITOR_PERMISSIONS

    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return MEMBER_PERMISSIONS


class VFolderWithPermissionSet(NamedTuple):
    vfolder_row: VFolderRow
    permissions: frozenset[VFolderRBACPermission]


async def get_vfolders(
    db_conn: SAConnection,
    ctx: ClientContext,
    target_scope: BaseScope,
    requested_permission: VFolderRBACPermission,
    extra_scope: StorageHost | None = None,
    *,
    vfolder_id: uuid.UUID | None = None,
    vfolder_name: str | None = None,
    usage_mode: VFolderUsageMode | None = None,
    allowed_status: Container[VFolderOperationStatus] | None = None,
    blocked_status: Container[VFolderOperationStatus] | None = None,
) -> list[VFolderWithPermissionSet]:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        host_permission = _VFOLDER_PERMISSION_TO_STORAGE_HOST_PERMISSION_MAP[requested_permission]
        host_permission_ctx = await StorageHostPermissionContextBuilder(db_session).build(
            ctx, target_scope, host_permission
        )
        builder = VFolderPermissionContextBuilder(db_session)
        permission_ctx = await builder.build(ctx, target_scope, requested_permission)
        permission_ctx.apply_host_permission_ctx(host_permission_ctx)

        query_stmt = await permission_ctx.build_query()
        if query_stmt is None:
            return []
        if vfolder_id is not None:
            query_stmt = query_stmt.where(VFolderRow.id == vfolder_id)
        if vfolder_name is not None:
            query_stmt = query_stmt.where(VFolderRow.name == vfolder_name)
        if usage_mode is not None:
            query_stmt = query_stmt.where(VFolderRow.usage_mode == usage_mode)
        if allowed_status is not None:
            query_stmt = query_stmt.where(VFolderRow.status.in_(allowed_status))
        if blocked_status is not None:
            query_stmt = query_stmt.where(VFolderRow.status.not_in(blocked_status))

        result: list[VFolderWithPermissionSet] = []
        for row in await db_session.scalars(query_stmt):
            row = cast(VFolderRow, row)
            permissions = await permission_ctx.calculate_final_permission(row)
            result.append(VFolderWithPermissionSet(row, permissions))
        return result


async def validate_permission(
    db_conn: SAConnection,
    ctx: ClientContext,
    target_scope: BaseScope,
    *,
    permission: VFolderRBACPermission,
    vfolder_id: uuid.UUID,
) -> None:
    vfolders = await get_vfolders(
        db_conn,
        ctx,
        target_scope,
        permission,
        vfolder_id=vfolder_id,
    )
    if not vfolders:
        raise NotEnoughPermission(f"'{permission.name}' not allowed in {str(target_scope)}")


async def get_permission_ctx(
    db_conn: SAConnection,
    ctx: ClientContext,
    target_scope: BaseScope,
    requested_permission: VFolderRBACPermission,
) -> VFolderPermissionContext:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        host_permission = _VFOLDER_PERMISSION_TO_STORAGE_HOST_PERMISSION_MAP[requested_permission]
        host_permission_ctx = await StorageHostPermissionContextBuilder(db_session).build(
            ctx, target_scope, host_permission
        )
        builder = VFolderPermissionContextBuilder(db_session)
        permission_ctx = await builder.build_in_nested_scope(
            ctx, target_scope, requested_permission
        )
        permission_ctx.apply_host_permission_ctx(host_permission_ctx)
    return permission_ctx
