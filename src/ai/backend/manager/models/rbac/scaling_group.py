import uuid
from dataclasses import dataclass
from typing import cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, selectinload

from ..domain import DomainRow
from ..group import GroupRow
from ..keypair import KeyPairRow
from ..scaling_group import ScalingGroupRow
from ..user import UserRow
from . import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    BaseScope,
    DomainScope,
    ProjectScope,
    UserScope,
    get_roles_in_scope,
)
from .context import ClientContext
from .exceptions import InvalidScope
from .permission_defs import ScalingGroupPermission

ALL_SCALING_GROUP_PERMISSIONS: frozenset[ScalingGroupPermission] = frozenset([
    perm for perm in ScalingGroupPermission
])
OWNER_PERMISSIONS: frozenset[ScalingGroupPermission] = ALL_SCALING_GROUP_PERMISSIONS
ADMIN_PERMISSIONS: frozenset[ScalingGroupPermission] = ALL_SCALING_GROUP_PERMISSIONS
MONITOR_PERMISSIONS: frozenset[ScalingGroupPermission] = ALL_SCALING_GROUP_PERMISSIONS
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[ScalingGroupPermission] = frozenset({
    ScalingGroupPermission.CREATE_COMPUTE_SESSION,
    ScalingGroupPermission.CREATE_MODEL_SERVICE_SESSION,
})
MEMBER_PERMISSIONS: frozenset[ScalingGroupPermission] = frozenset({
    ScalingGroupPermission.CREATE_COMPUTE_SESSION,
    ScalingGroupPermission.CREATE_MODEL_SERVICE_SESSION,
})


@dataclass
class PermissionContext(AbstractPermissionContext[ScalingGroupPermission, str, str]):
    async def build_query(self) -> sa.sql.Select | None:
        return None

    async def calculate_final_permission(self, rbac_obj: str) -> frozenset[ScalingGroupPermission]:
        host_name = rbac_obj
        return self.object_id_to_additional_permission_map.get(host_name, frozenset())


class PermissionContextBuilder(
    AbstractPermissionContextBuilder[ScalingGroupPermission, PermissionContext]
):
    db_session: SASession

    def __init__(self, db_session: SASession) -> None:
        self.db_session = db_session

    async def build(
        self,
        ctx: ClientContext,
        target_scope: BaseScope,
        requested_permission: ScalingGroupPermission,
    ) -> PermissionContext:
        match target_scope:
            case DomainScope(domain_name):
                permission_ctx = await self.build_in_domain_scope(ctx, domain_name)
            case ProjectScope(project_id, _):
                permission_ctx = await self.build_in_project_scope(ctx, project_id)
            case UserScope(user_id, _):
                permission_ctx = await self.build_in_user_scope(ctx, user_id)
            case _:
                raise InvalidScope
        permission_ctx.filter_by_permission(requested_permission)
        return permission_ctx

    async def build_in_domain_scope(
        self,
        ctx: ClientContext,
        domain_name: str,
    ) -> PermissionContext:
        roles = await get_roles_in_scope(ctx, DomainScope(domain_name), self.db_session)
        domain_permissions = await self.calculate_permission_by_roles(roles)
        if not domain_permissions:
            # User is not part of the domain.
            return PermissionContext()

        stmt = (
            sa.select(DomainRow)
            .where(DomainRow.name == domain_name)
            .options(selectinload(DomainRow.scaling_groups))
        )
        domain_row = cast(DomainRow | None, await self.db_session.scalar(stmt))
        if domain_row is None:
            return PermissionContext()
        scaling_groups = cast(list[ScalingGroupRow], domain_row.scaling_groups)
        result = PermissionContext(
            object_id_to_additional_permission_map={
                row.name: domain_permissions for row in scaling_groups
            }
        )
        return result

    async def build_in_project_scope(
        self,
        ctx: ClientContext,
        project_id: uuid.UUID,
    ) -> PermissionContext:
        roles = await get_roles_in_scope(ctx, ProjectScope(project_id), self.db_session)
        project_permissions = await self.calculate_permission_by_roles(roles)
        if not project_permissions:
            # User is not part of the domain.
            return PermissionContext()

        stmt = (
            sa.select(GroupRow)
            .where(GroupRow.id == project_id)
            .options(selectinload(GroupRow.scaling_groups))
        )
        project_row = cast(GroupRow | None, await self.db_session.scalar(stmt))
        if project_row is None:
            return PermissionContext()
        scaling_groups = cast(list[ScalingGroupRow], project_row.scaling_groups)
        result = PermissionContext(
            object_id_to_additional_permission_map={
                row.name: project_permissions for row in scaling_groups
            }
        )
        return result

    async def build_in_user_scope(
        self,
        ctx: ClientContext,
        user_id: uuid.UUID,
    ) -> PermissionContext:
        roles = await get_roles_in_scope(ctx, UserScope(user_id), self.db_session)
        user_permissions = await self.calculate_permission_by_roles(roles)
        if not user_permissions:
            # User is not part of the domain.
            return PermissionContext()

        stmt = (
            sa.select(UserRow)
            .where(UserRow.uuid == user_id)
            .options(selectinload(UserRow.keypairs).options(joinedload(KeyPairRow.scaling_groups)))
        )
        user_row = cast(UserRow | None, await self.db_session.scalar(stmt))
        if user_row is None:
            return PermissionContext()

        object_id_to_additional_permission_map: dict[str, frozenset[ScalingGroupPermission]] = {}
        for keypair in user_row.keypairs:
            scaling_groups = cast(list[ScalingGroupRow], keypair.scaling_groups)
            for sg in scaling_groups:
                if sg.name not in object_id_to_additional_permission_map:
                    object_id_to_additional_permission_map[sg.name] = user_permissions
        result = PermissionContext(
            object_id_to_additional_permission_map=object_id_to_additional_permission_map
        )
        return result

    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return OWNER_PERMISSIONS

    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return ADMIN_PERMISSIONS

    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return MONITOR_PERMISSIONS

    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[ScalingGroupPermission]:
        return MEMBER_PERMISSIONS
