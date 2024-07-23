from __future__ import annotations

import logging
import uuid
from collections.abc import Container, Mapping
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Sequence,
    TypeAlias,
    cast,
)

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import load_only

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import (
    VFolderUsageMode,
)

from ..group import GroupRow
from ..rbac import (
    UserScope as UserRBACScope,
)
from ..user import UserRole
from ..vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermissionRow,
    VFolderRow,
)
from ..vfolder import VFolderPermission as VFolderLegacyPermission
from . import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    BaseScope,
    ClientContext,
    DomainScope,
    ProjectScope,
    ScopedUserRole,
    StorageHost,
    get_roles_in_scope,
)
from .exceptions import InvalidScope, NotEnoughPermission
from .permission_defs import VFolderPermission

if TYPE_CHECKING:
    pass

__all__: Sequence[str] = (
    "get_vfolders",
    "VFolderWithPermissionSet",
    "OWNER_PERMISSIONS",
    "VFolderPermissionContext",
    "VFolderPermissionContextBuilder",
)


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)
# TypeAlias is deprecated since 3.12

OWNER_PERMISSIONS: frozenset[VFolderPermission] = frozenset([perm for perm in VFolderPermission])
ADMIN_PERMISSIONS: frozenset[VFolderPermission] = frozenset([
    VFolderPermission.READ_ATTRIBUTE,
    VFolderPermission.UPDATE_ATTRIBUTE,
    VFolderPermission.DELETE_VFOLDER,
])
MONITOR_PERMISSIONS: frozenset[VFolderPermission] = frozenset([
    VFolderPermission.READ_ATTRIBUTE,
    VFolderPermission.UPDATE_ATTRIBUTE,
])
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[VFolderPermission] = frozenset([
    VFolderPermission.READ_ATTRIBUTE,
    VFolderPermission.READ_CONTENT,
    VFolderPermission.WRITE_CONTENT,
    VFolderPermission.DELETE_CONTENT,
    VFolderPermission.MOUNT_RO,
    VFolderPermission.MOUNT_RW,
    VFolderPermission.MOUNT_WD,
])
MEMBER_PERMISSIONS: frozenset[VFolderPermission] = frozenset()

# TODO: Change type of `vfolder_permissions.permission` to VFolderPermission
LEGACY_PERMISSION_TO_RBAC_PERMISSION_MAP: Mapping[
    VFolderLegacyPermission, frozenset[VFolderPermission]
] = {
    VFolderLegacyPermission.READ_ONLY: frozenset([
        VFolderPermission.READ_ATTRIBUTE,
        VFolderPermission.READ_CONTENT,
    ]),
    VFolderLegacyPermission.READ_WRITE: frozenset([
        VFolderPermission.READ_ATTRIBUTE,
        VFolderPermission.UPDATE_ATTRIBUTE,
        VFolderPermission.DELETE_VFOLDER,
        VFolderPermission.READ_CONTENT,
        VFolderPermission.WRITE_CONTENT,
        VFolderPermission.DELETE_CONTENT,
        VFolderPermission.MOUNT_RO,
        VFolderPermission.MOUNT_RW,
    ]),
    VFolderLegacyPermission.RW_DELETE: frozenset([
        VFolderPermission.READ_ATTRIBUTE,
        VFolderPermission.UPDATE_ATTRIBUTE,
        VFolderPermission.DELETE_VFOLDER,
        VFolderPermission.READ_CONTENT,
        VFolderPermission.WRITE_CONTENT,
        VFolderPermission.DELETE_CONTENT,
        VFolderPermission.MOUNT_RO,
        VFolderPermission.MOUNT_RW,
        VFolderPermission.MOUNT_WD,
    ]),
    VFolderLegacyPermission.OWNER_PERM: frozenset(OWNER_PERMISSIONS),
}


@dataclass
class VFolderPermissionContext(AbstractPermissionContext[VFolderPermission, VFolderRow, uuid.UUID]):
    @property
    def query_condition(self) -> WhereClauseType | None:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        def _AND_coalesce(
            base_cond: WhereClauseType | None,
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond & _cond if base_cond is not None else _cond

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
        return cond

    async def build_query(self) -> sa.sql.Select | None:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(VFolderRow).where(cond)

    async def calculate_final_permission(
        self, rbac_obj: VFolderRow
    ) -> frozenset[VFolderPermission]:
        vfolder_row = rbac_obj
        vfolder_id = cast(uuid.UUID, vfolder_row.id)
        permissions: set[VFolderPermission] = set()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(vfolder_id)
        ) is not None:
            permissions = set(overriding_perm)
        else:
            permissions |= self.object_id_to_additional_permission_map.get(vfolder_id, set())
            permissions |= self.user_id_to_permission_map.get(vfolder_row.user, set())
            permissions |= self.project_id_to_permission_map.get(vfolder_row.group, set())
            permissions |= self.domain_name_to_permission_map.get(vfolder_row.domain_name, set())

        return frozenset(permissions)


class VFolderPermissionContextBuilder(
    AbstractPermissionContextBuilder[VFolderPermission, VFolderPermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    async def build(
        self,
        ctx: ClientContext,
        target_scope: BaseScope,
        requested_permission: VFolderPermission,
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
        requested_permission: VFolderPermission,
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
            case ProjectScope(project_id, domain_name):
                permission_ctx = await self.build_in_project_scope(ctx, project_id)
                if domain_name is not None:
                    _user_perm_ctx = await self.build_in_user_scope_in_domain(
                        ctx, ctx.user_id, domain_name
                    )
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
    ) -> frozenset[VFolderPermission]:
        return OWNER_PERMISSIONS

    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[VFolderPermission]:
        return ADMIN_PERMISSIONS

    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[VFolderPermission]:
        return MONITOR_PERMISSIONS

    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[VFolderPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[VFolderPermission]:
        return MEMBER_PERMISSIONS


class VFolderWithPermissionSet(NamedTuple):
    vfolder_row: VFolderRow
    permissions: frozenset[VFolderPermission]


async def get_vfolders(
    db_conn: SAConnection,
    ctx: ClientContext,
    target_scope: BaseScope,
    requested_permission: VFolderPermission,
    extra_scope: StorageHost | None = None,
    *,
    vfolder_id: uuid.UUID | None = None,
    vfolder_name: str | None = None,
    usage_mode: VFolderUsageMode | None = None,
    allowed_status: Container[VFolderOperationStatus] | None = None,
    blocked_status: Container[VFolderOperationStatus] | None = None,
) -> list[VFolderWithPermissionSet]:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        builder = VFolderPermissionContextBuilder(db_session)
        permission_ctx = await builder.build(ctx, target_scope, requested_permission)

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
    permission: VFolderPermission,
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
