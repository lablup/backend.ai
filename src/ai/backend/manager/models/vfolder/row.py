from __future__ import annotations

import logging
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    Final,
    NamedTuple,
    cast,
    override,
)

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import Mapped, foreign, load_only, mapped_column, relationship, selectinload

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.entity.vfolder_mount_policy import VFolderMountPolicyID
from ai.backend.common.defs import MODEL_VFOLDER_LENGTH_LIMIT
from ai.backend.common.types import (
    QuotaScopeID,
    VFolderID,
    VFolderMountPolicy,
    VFolderUsageMode,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.data.permission.permission_defs import StorageHostPermission
from ai.backend.manager.data.permission.permission_defs import (
    VFolderPermission as VFolderRBACPermission,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import (
    VFolderNotFound,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    EnumValueType,
    QuotaScopeIDType,
    StrEnumType,
    metadata,
)
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    ScopeType,
    StorageHost,
    get_predefined_roles_in_scope,
)
from ai.backend.manager.models.rbac import (
    UserScope as UserRBACScope,
)
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.storage import PermissionContext as StorageHostPermissionContext
from ai.backend.manager.models.storage import (
    PermissionContextBuilder as StorageHostPermissionContextBuilder,
)
from ai.backend.manager.models.user.row import UserRole, UserRow
from ai.backend.manager.models.virtual_entity.queries import (
    user_scope_membership_exists,
)

__all__: Sequence[str] = (
    "VFolderRow",
    "VFolderUserMountPolicyRow",
)


log = StructuredLogger(logging.getLogger(__spec__.name))


def _get_user_row_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    return UserRow.uuid == foreign(VFolderRow.user)


def _get_group_row_join_condition() -> sa.sql.elements.ColumnElement[Any]:
    return ProjectRow.id == foreign(VFolderRow.group)


#: The name of the index holding a folder name unique within its project. Named here
#: so the spec that maps its violation and the migration that creates it agree.
VFOLDER_NAME_IN_PROJECT_INDEX: Final = "uq_vfolders_project_name"


class VFolderRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "vfolders"
    __table_args__ = (
        # A folder name stands once in the project it was created in. A folder whose
        # storage payload is gone leaves its name behind for the next one.
        sa.Index(
            VFOLDER_NAME_IN_PROJECT_INDEX,
            "group",
            "name",
            unique=True,
            postgresql_where=sa.text(
                "status NOT IN ('delete-complete', 'delete-error')",
            ),
        ),
    )

    id: Mapped[VFolderUUID] = mapped_column(
        "id",
        GUID(VFolderUUID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    # host will be '' if vFolder is unmanaged
    host: Mapped[str] = mapped_column("host", sa.String(length=128), nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), nullable=False, index=True
    )
    quota_scope_id: Mapped[QuotaScopeID] = mapped_column(
        "quota_scope_id", QuotaScopeIDType, nullable=False
    )
    name: Mapped[str] = mapped_column(
        "name", sa.String(length=MODEL_VFOLDER_LENGTH_LIMIT), nullable=False, index=True
    )
    usage_mode: Mapped[VFolderUsageMode] = mapped_column(
        "usage_mode",
        EnumValueType(VFolderUsageMode),
        default=VFolderUsageMode.GENERAL,
        nullable=False,
        index=True,
    )
    default_mount_permission: Mapped[VFolderMountPolicy] = mapped_column(
        "default_mount_permission",
        StrEnumType(VFolderMountPolicy),
        nullable=False,
        default=VFolderMountPolicy.READ_WRITE,
    )
    max_files: Mapped[int | None] = mapped_column("max_files", sa.Integer(), default=1000)
    max_size: Mapped[int | None] = mapped_column(
        "max_size", sa.Integer(), default=None
    )  # in MBytes
    num_files: Mapped[int | None] = mapped_column("num_files", sa.Integer(), default=0)
    cur_size: Mapped[int | None] = mapped_column("cur_size", sa.Integer(), default=0)  # in KBytes
    last_used: Mapped[datetime | None] = mapped_column(
        "last_used", sa.DateTime(timezone=True), nullable=True
    )
    # creator is always set to the user who created vfolder (regardless user/project types)
    creator: Mapped[str | None] = mapped_column("creator", sa.String(length=128), nullable=True)
    creator_id: Mapped[UserID | None] = mapped_column("creator_id", GUID(UserID), nullable=True)
    # unmanaged vfolder represents the host-side absolute path instead of storage-based path.
    unmanaged_path: Mapped[str | None] = mapped_column(
        "unmanaged_path", sa.String(length=512), nullable=True
    )
    ownership_type: Mapped[VFolderOwnershipType] = mapped_column(
        "ownership_type",
        EnumValueType(VFolderOwnershipType),
        default=VFolderOwnershipType.USER,
        nullable=False,
        index=True,
    )
    user: Mapped[UserID | None] = mapped_column(
        "user", GUID(UserID), nullable=True
    )  # owner if user vfolder
    group: Mapped[ProjectID | None] = mapped_column(
        "group", GUID(ProjectID), nullable=True
    )  # owner if project vfolder
    cloneable: Mapped[bool] = mapped_column("cloneable", sa.Boolean, default=False, nullable=False)
    status: Mapped[VFolderOperationStatus] = mapped_column(
        "status",
        StrEnumType(VFolderOperationStatus),
        default=VFolderOperationStatus.READY,
        server_default=VFolderOperationStatus.READY,
        nullable=False,
        index=True,
    )
    # status_history records the most recent status changes for each status
    # e.g)
    # {
    #   "ready": "2022-10-22T10:22:30",
    #   "delete-pending": "2022-10-22T11:40:30",
    #   "delete-ongoing": "2022-10-25T10:22:30"
    # }
    status_history: Mapped[dict[str, Any] | None] = mapped_column(
        "status_history", pgsql.JSONB(), nullable=True, default=sa.null()
    )
    status_changed: Mapped[datetime | None] = mapped_column(
        "status_changed", sa.DateTime(timezone=True), nullable=True, index=True
    )

    # Relationships
    # Read only by VFolderRow.get and gql_legacy (endpoint.py, vfolder.py).
    # Delete it together with the gql_legacy cleanup.
    user_row: Mapped[UserRow | None] = relationship(
        "UserRow",
        primaryjoin=_get_user_row_join_condition,
    )
    # Read only by VFolderRow.get and gql_legacy (endpoint.py, vfolder.py).
    # Delete it together with the gql_legacy cleanup.
    group_row: Mapped[ProjectRow | None] = relationship(
        "ProjectRow",
        primaryjoin=_get_group_row_join_condition,
    )

    # Called only by gql_legacy (endpoint.py, vfolder.py).
    # Delete it together with the gql_legacy cleanup.
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
            raise VFolderNotFound()
        return result

    def __contains__(self, key: str) -> bool:
        return key in self.__dir__()

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError as e:
            raise KeyError(item) from e

    @property
    def vfid(self) -> VFolderID:
        return VFolderID(self.quota_scope_id, self.id)


# NOTE: Deprecated legacy table reference for backward compatibility.
# Use VFolderRow class directly for new code.
vfolders = VFolderRow.__table__


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


class VFolderUserMountPolicyRow(LifecycleTimestampsMixin, Base):
    """The mount level one user gets on a vfolder, set by whoever may update the folder.

    Stands apart from access: it takes effect only while the user can read the folder,
    and a share ending leaves it in place.
    """

    __tablename__ = "vfolder_user_mount_policies"
    __table_args__ = (sa.UniqueConstraint("vfolder_id", "user_id"),)

    id: Mapped[VFolderMountPolicyID] = mapped_column(
        "id",
        GUID(VFolderMountPolicyID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    vfolder_id: Mapped[VFolderUUID] = mapped_column(
        "vfolder_id",
        GUID(VFolderUUID),
        sa.ForeignKey("vfolders.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UserID] = mapped_column(
        "user_id",
        GUID(UserID),
        sa.ForeignKey("users.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    permission: Mapped[VFolderMountPolicy] = mapped_column(
        "permission", StrEnumType(VFolderMountPolicy), nullable=False
    )


# Called by gql_legacy (schema.py, vfolder.py) and VfolderRepository.validate_quota_scope_access.
# Move it into the repository together with the gql_legacy cleanup.
async def ensure_quota_scope_accessible_by_user(
    conn: SASession,
    quota_scope: QuotaScopeID,
    user: Mapping[str, Any],
) -> None:
    # Lookup user table to match if quota is scoped to the user
    user_query = sa.select(UserRow).where(UserRow.uuid == quota_scope.scope_id)
    quota_scope_user: UserRow | None = await conn.scalar(user_query)
    if quota_scope_user:
        match user["role"]:
            case UserRole.SUPERADMIN:
                return
            case UserRole.ADMIN:
                if quota_scope_user.domain_name == user["domain_name"]:
                    return
            case _:
                if quota_scope_user.uuid == user["uuid"]:
                    return
        raise InvalidAPIParameters

    # Lookup group table to match if quota is scoped to the group
    group_query = sa.select(ProjectRow).where(ProjectRow.id == quota_scope.scope_id)
    quota_scope_group: ProjectRow | None = await conn.scalar(group_query)
    if quota_scope_group:
        match user["role"]:
            case UserRole.SUPERADMIN:
                return
            case UserRole.ADMIN:
                if quota_scope_group.domain_name == user["domain_name"]:
                    return
            case _:
                membership_query = sa.select(
                    user_scope_membership_exists(
                        ProjectEntityType(), quota_scope_group.id, user["uuid"]
                    )
                )
                if await conn.scalar(membership_query):
                    return

    raise InvalidAPIParameters


# Note: GraphQL classes (VirtualFolder, VirtualFolderList, VirtualFolderPermission,
# VirtualFolderPermissionList, QuotaDetails, QuotaScope, QuotaScopeInput, SetQuotaScope,
# UnsetQuotaScope) have been moved to api/gql_legacy/vfolder.py

# RBAC
type WhereClauseType = sa.sql.expression.BinaryExpression[Any] | sa.sql.expression.BooleanClauseList
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

MOUNT_POLICY_TO_RBAC_PERMISSION_MAP: Mapping[
    VFolderMountPolicy, frozenset[VFolderRBACPermission]
] = {
    VFolderMountPolicy.NONE: frozenset([
        VFolderRBACPermission.READ_ATTRIBUTE,
        VFolderRBACPermission.READ_CONTENT,
    ]),
    VFolderMountPolicy.READ_ONLY: frozenset([
        VFolderRBACPermission.READ_ATTRIBUTE,
        VFolderRBACPermission.READ_CONTENT,
        VFolderRBACPermission.MOUNT_RO,
    ]),
    VFolderMountPolicy.READ_WRITE: frozenset([
        VFolderRBACPermission.READ_ATTRIBUTE,
        VFolderRBACPermission.UPDATE_ATTRIBUTE,
        VFolderRBACPermission.READ_CONTENT,
        VFolderRBACPermission.WRITE_CONTENT,
        VFolderRBACPermission.DELETE_CONTENT,
        VFolderRBACPermission.MOUNT_RO,
        VFolderRBACPermission.MOUNT_RW,
    ]),
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
    AbstractPermissionContext[VFolderRBACPermission, VFolderRow, VFolderUUID]
):
    host_permission_ctx: StorageHostPermissionContext | None = None

    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression[Any],
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

    @override
    async def build_query(self) -> sa.sql.Select[Any] | None:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(VFolderRow).where(cond)

    @override
    async def calculate_final_permission(
        self, rbac_obj: VFolderRow
    ) -> frozenset[VFolderRBACPermission]:
        vfolder_row = rbac_obj
        vfolder_id = vfolder_row.id
        permissions: set[VFolderRBACPermission] = set()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(vfolder_id)
        ) is not None:
            permissions = set(overriding_perm)
        else:
            permissions |= self.object_id_to_additional_permission_map.get(vfolder_id, set())
            if vfolder_row.user is not None:
                permissions |= self.user_id_to_permission_map.get(vfolder_row.user, set())
            if vfolder_row.group is not None:
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

        match vfolder_row.default_mount_permission:
            case VFolderMountPolicy.READ_WRITE:
                pass
            case VFolderMountPolicy.READ_ONLY:
                permissions -= {VFolderRBACPermission.MOUNT_RW, VFolderRBACPermission.MOUNT_WD}
            case VFolderMountPolicy.NONE:
                permissions -= {
                    VFolderRBACPermission.MOUNT_RO,
                    VFolderRBACPermission.MOUNT_RW,
                    VFolderRBACPermission.MOUNT_WD,
                }
        return frozenset(permissions)


class VFolderPermissionContextBuilder(
    AbstractPermissionContextBuilder[VFolderRBACPermission, VFolderPermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[VFolderRBACPermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        return await self._calculate_permission_by_predefined_roles(roles)

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> VFolderPermissionContext:
        from ai.backend.manager.models.domain.row import DomainRow

        perm_ctx = VFolderPermissionContext()
        _domain_query_stmt = sa.select(DomainRow).options(load_only(DomainRow.name))
        for row in await self.db_session.scalars(_domain_query_stmt):
            to_be_merged = await self.build_ctx_in_domain_scope(ctx, DomainScope(row.name))
            perm_ctx.merge(to_be_merged)
        return perm_ctx

    @override
    async def build_ctx_in_domain_scope(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> VFolderPermissionContext:
        permission_ctx = await self._build_at_domain_scope_non_recursively(ctx, scope.domain_name)
        _user_perm_ctx = await self._build_at_user_scope_in_domain(
            ctx, ctx.user_id, scope.domain_name
        )
        permission_ctx.merge(_user_perm_ctx)
        _project_perm_ctx = await self._build_at_project_scopes_in_domain(ctx, scope.domain_name)
        permission_ctx.merge(_project_perm_ctx)
        return permission_ctx

    @override
    async def build_ctx_in_project_scope(
        self, ctx: ClientContext, scope: ProjectScope
    ) -> VFolderPermissionContext:
        permission_ctx = await self._build_at_project_scope_non_recursively(ctx, scope.project_id)
        _user_perm_ctx = await self._build_at_user_scope_non_recursively(ctx, ctx.user_id)
        permission_ctx.merge(_user_perm_ctx)
        return permission_ctx

    @override
    async def build_ctx_in_user_scope(
        self, ctx: ClientContext, scope: UserRBACScope
    ) -> VFolderPermissionContext:
        return await self._build_at_user_scope_non_recursively(ctx, scope.user_id)

    async def _lent_folder_permissions(
        self,
        user_id: uuid.UUID,
        ownership_type: VFolderOwnershipType,
        domain_name: str | None = None,
    ) -> dict[VFolderUUID, frozenset[VFolderRBACPermission]]:
        """The legacy permission set on each folder lent to the user, from the mount
        level they get: their policy row, or the folder's default."""
        stmt = (
            sa.select(
                EntityShareRow.target_entity_id,
                sa.func.coalesce(
                    VFolderUserMountPolicyRow.permission, VFolderRow.default_mount_permission
                ),
            )
            .select_from(EntityShareRow)
            .join(VFolderRow, VFolderRow.id == EntityShareRow.target_entity_id)
            .outerjoin(
                VFolderUserMountPolicyRow,
                sa.and_(
                    VFolderUserMountPolicyRow.vfolder_id == VFolderRow.id,
                    VFolderUserMountPolicyRow.user_id == user_id,
                ),
            )
            .where(
                EntityShareRow.target_entity_type == VFolderEntityType(),
                EntityShareRow.recipient_entity_type == UserEntityType(),
                EntityShareRow.recipient_entity_id == user_id,
                EntityShareRow.status == EntityShareStatus.ACCEPTED,
                VFolderRow.ownership_type == ownership_type,
            )
        )
        if domain_name is not None:
            stmt = stmt.where(VFolderRow.domain_name == domain_name)
        return {
            VFolderUUID(row.target_entity_id): MOUNT_POLICY_TO_RBAC_PERMISSION_MAP[
                VFolderMountPolicy(row[1])
            ]
            for row in (await self.db_session.execute(stmt)).all()
        }

    async def _build_at_domain_scope_non_recursively(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> VFolderPermissionContext:
        domain_permissions = await self.calculate_permission(ctx, DomainScope(domain_name))
        return VFolderPermissionContext(
            domain_name_to_permission_map={domain_name: domain_permissions}
        )

    async def _build_at_project_scopes_in_domain(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> VFolderPermissionContext:
        result = VFolderPermissionContext()

        _project_stmt = (
            sa.select(ProjectRow)
            .where(
                ProjectRow.domain_name == domain_name,
                user_scope_membership_exists(ProjectEntityType(), ProjectRow.id, ctx.user_id),
            )
            .options(load_only(ProjectRow.id))
        )
        for row in await self.db_session.scalars(_project_stmt):
            _row = row
            _project_perm_ctx = await self._build_at_project_scope_non_recursively(ctx, _row.id)
            result.merge(_project_perm_ctx)
        return result

    async def _build_at_user_scope_in_domain(
        self,
        ctx: ClientContext,
        user_id: uuid.UUID,
        domain_name: str,
    ) -> VFolderPermissionContext:
        # For Superadmin and monitor who can create vfolders in multiple different domains.
        permissions = await self.calculate_permission(ctx, UserRBACScope(user_id, domain_name))

        _vfolder_stmt = (
            sa.select(VFolderRow)
            .where((VFolderRow.user == user_id) & (VFolderRow.domain_name == domain_name))
            .options(load_only(VFolderRow.id))
        )
        own_folder_map = {
            row.id: permissions for row in await self.db_session.scalars(_vfolder_stmt)
        }
        result = VFolderPermissionContext(object_id_to_additional_permission_map=own_folder_map)

        object_id_to_permission_map = await self._lent_folder_permissions(
            ctx.user_id, VFolderOwnershipType.USER, domain_name
        )
        if ctx.user_role in (UserRole.SUPERADMIN, UserRole.ADMIN):
            ctx_to_merge = VFolderPermissionContext(
                object_id_to_additional_permission_map=object_id_to_permission_map
            )
        else:
            ctx_to_merge = VFolderPermissionContext(
                object_id_to_overriding_permission_map=object_id_to_permission_map
            )
        result.merge(ctx_to_merge)
        return result

    async def _build_at_project_scope_non_recursively(
        self,
        ctx: ClientContext,
        project_id: uuid.UUID,
    ) -> VFolderPermissionContext:
        permissions = await self.calculate_permission(ctx, ProjectScope(project_id))
        result = VFolderPermissionContext(project_id_to_permission_map={project_id: permissions})

        object_id_to_permission_map = await self._lent_folder_permissions(
            ctx.user_id, VFolderOwnershipType.GROUP
        )
        if ctx.user_role in (UserRole.ADMIN, UserRole.SUPERADMIN):
            result.object_id_to_additional_permission_map = object_id_to_permission_map
        else:
            result.object_id_to_overriding_permission_map = object_id_to_permission_map
        return result

    async def _build_at_user_scope_non_recursively(
        self,
        ctx: ClientContext,
        user_id: uuid.UUID,
    ) -> VFolderPermissionContext:
        permissions = await self.calculate_permission(ctx, UserRBACScope(user_id))
        result = VFolderPermissionContext(user_id_to_permission_map={user_id: permissions})

        object_id_to_permission_map = await self._lent_folder_permissions(
            ctx.user_id, VFolderOwnershipType.USER
        )
        if ctx.user_role in (UserRole.SUPERADMIN, UserRole.ADMIN):
            result.object_id_to_additional_permission_map = object_id_to_permission_map
        else:
            result.object_id_to_overriding_permission_map = object_id_to_permission_map
        return result

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[VFolderRBACPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
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
    target_scope: ScopeType,
    requested_permission: VFolderRBACPermission,
    _extra_scope: StorageHost | None = None,
    *,
    vfolder_id: uuid.UUID | None = None,
    vfolder_name: str | None = None,
    usage_mode: VFolderUsageMode | None = None,
    allowed_status: Iterable[VFolderOperationStatus] | None = None,
    blocked_status: Iterable[VFolderOperationStatus] | None = None,
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


async def get_permission_ctx(
    db_conn: SAConnection,
    ctx: ClientContext,
    target_scope: ScopeType,
    requested_permission: VFolderRBACPermission,
) -> VFolderPermissionContext:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        builder = VFolderPermissionContextBuilder(db_session)
        return await builder.build(ctx, target_scope, requested_permission)
        # TODO: Plan how to check storage host permission with recursive scopes
        # host_permission = _VFOLDER_PERMISSION_TO_STORAGE_HOST_PERMISSION_MAP[requested_permission]
        # host_permission_ctx = await StorageHostPermissionContextBuilder(db_session).build(
        #     ctx, target_scope, host_permission
        # )
        # permission_ctx.apply_host_permission_ctx(host_permission_ctx)
