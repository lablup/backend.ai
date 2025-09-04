import uuid
from typing import Optional, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.metrics.metric import LayerType

from ...data.permission.id import (
    ObjectId,
)
from ...data.permission.role import (
    PermissionCheckInput,
    RoleCreateInput,
    RoleData,
    RoleDataWithPermissions,
    RoleDeleteInput,
    RoleUpdateInput,
    UserRoleAssignmentInput,
)
from ...data.permission.status import (
    RoleStatus,
)
from ...decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ...errors.common import ObjectNotFound
from ...models.rbac_models.object_permission import ObjectPermissionRow
from ...models.rbac_models.role import RoleRow
from ...models.rbac_models.scope_permission import ScopePermissionRow
from ...models.rbac_models.user_role import UserRoleRow
from ...models.utils import ExtendedAsyncSAEngine

# Layer-specific decorator for user repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.PERMISSION_CONTROL)


class PermissionControllerRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def create_role(self, data: RoleCreateInput) -> RoleData:
        """
        Create a new role in the database.

        Returns the ID of the created role.
        """
        async with self._db.begin_session() as db_session:
            role_row = RoleRow.from_input(data)
            db_session.add(role_row)  # type: ignore[arg-type]
            await db_session.flush()
            role_id = role_row.id
            for scope_permission in data.scope_permissions:
                scope_permission_row = ScopePermissionRow(
                    role_id=role_id,
                    entity_type=scope_permission.entity_type,
                    operation=scope_permission.operation,
                )
                db_session.add(scope_permission_row)  # type: ignore[arg-type]
            for object_permission in data.object_permissions:
                object_permission_row = ObjectPermissionRow(
                    role_id=role_id,
                    entity_type=object_permission.object_id.entity_type,
                    entity_id=object_permission.object_id.entity_id,
                    operation=object_permission.operation,
                )
                db_session.add(object_permission_row)  # type: ignore[arg-type]
            await db_session.commit()
        return role_row.to_data()

    async def _get_role(self, role_id: uuid.UUID, db_session: SASession) -> Optional[RoleRow]:
        stmt = sa.select(RoleRow).where(RoleRow.id == role_id)
        role_row = await db_session.scalar(stmt)
        return cast(Optional[RoleRow], role_row)

    @repository_decorator()
    async def update_role(self, data: RoleUpdateInput) -> RoleData:
        to_update = data.fields_to_update()
        async with self._db.begin_session() as db_session:
            stmt = sa.update(RoleRow).where(RoleRow.id == data.id).values(**to_update)
            await db_session.execute(stmt)
            role_row = await self._get_role(data.id, db_session)
            if role_row is None:
                raise ObjectNotFound(f"Role with ID {data.id} does not exist.")
            return role_row.to_data()

    @repository_decorator()
    async def delete_role(self, data: RoleDeleteInput) -> RoleData:
        async with self._db.begin_session() as db_session:
            role_row = await self._get_role(data.id, db_session)
            if role_row is None:
                raise ObjectNotFound(f"Role with ID {data.id} does not exist.")
            role_row.status = RoleStatus.DELETED
            role_data = role_row.to_data()
        return role_data

    @repository_decorator()
    async def assign_role(self, data: UserRoleAssignmentInput):
        async with self._db.begin_session() as db_session:
            user_role_row = UserRoleRow.from_input(data)
            db_session.add(user_role_row)
        return user_role_row.to_data()

    @repository_decorator()
    async def get_role(self, role_id: uuid.UUID) -> Optional[RoleData]:
        async with self._db.begin_readonly_session() as db_session:
            result = await self._get_role(role_id, db_session)
            if result is None:
                return None
            return result.to_data()

    @repository_decorator()
    async def get_active_roles(self, user_id: uuid.UUID) -> list[RoleDataWithPermissions]:
        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(RoleRow)
                .join(UserRoleRow, RoleRow.id == UserRoleRow.role_id)
                .where(
                    sa.and_(
                        RoleRow.status == RoleStatus.ACTIVE,
                        UserRoleRow.user_id == user_id,
                    )
                )
                .options(
                    selectinload(RoleRow.scope_permission_rows).options(
                        selectinload(ScopePermissionRow.mapped_entity_rows)
                    ),
                    selectinload(RoleRow.object_permission_rows),
                )
            )
            result = await db_session.scalars(query)
            result = cast(list[RoleRow], result)
            return [role.to_data_with_permissions() for role in result]

    @repository_decorator()
    async def check_permission(self, data: PermissionCheckInput) -> bool:
        roles = await self.get_active_roles(data.user_id)
        target_object_id = ObjectId(
            entity_type=data.target_entity_type,
            entity_id=data.target_entity_id,
        )
        for role in roles:
            for scope_perm in role.scope_permissions:
                if scope_perm.operation != data.operation:
                    continue
                for entity in scope_perm.mapped_entities:
                    obj_id = ObjectId(
                        entity_type=scope_perm.entity_type,
                        entity_id=entity.entity_id,
                    )
                    if obj_id == target_object_id:
                        return True
            for object_perm in role.object_permissions:
                if object_perm.operation != data.operation:
                    continue
                if object_perm.object_id == target_object_id:
                    return True

        return False
