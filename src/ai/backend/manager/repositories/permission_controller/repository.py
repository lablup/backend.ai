import uuid
from typing import Optional, cast

import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from ai.backend.manager.errors.exceptions import ObjectNotFound
from ai.backend.manager.internal_types.permission_controller.role import (
    RoleCreateInput,
    RoleData,
    RoleDataWithPermissions,
    RoleDeleteInput,
    RoleUpdateInput,
    UserRoleAssignmentInput,
)
from ai.backend.manager.internal_types.permission_controller.status import (
    RoleStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from ...models.rbac_models.object_permission import ObjectPermissionRow
from ...models.rbac_models.role import RoleRow
from ...models.rbac_models.scope_permission import ScopePermissionRow
from ...models.rbac_models.user_role import UserRoleRow


class PermissionControllerRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

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
                    scope_type=scope_permission.scope_id.scope_type,
                    scope_id=scope_permission.scope_id.scope_id,
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

    async def update_role(self, data: RoleUpdateInput) -> RoleData:
        async with self._db.begin_session() as db_session:
            stmt = sa.select(RoleRow).where(RoleRow.id == data.id)
            role_row = await db_session.scalar(stmt)
            role_row = cast(Optional[RoleRow], role_row)
            if role_row is None:
                raise ObjectNotFound(f"Role with ID {data.id} does not exist.")
            role_row.update(data)
        return role_row.to_data()

    async def delete_role(self, data: RoleDeleteInput) -> RoleData:
        async with self._db.begin_session() as db_session:
            stmt = sa.select(RoleRow).where(RoleRow.id == data.id)
            role_row = await db_session.scalar(stmt)
            role_row = cast(Optional[RoleRow], role_row)
            if role_row is None:
                raise ObjectNotFound(f"Role with ID {data.id} does not exist.")
            role_row.status = RoleStatus.DELETED
            role_data = role_row.to_data()
        return role_data

    async def assign_role(self, data: UserRoleAssignmentInput):
        async with self._db.begin_session() as db_session:
            user_role_row = UserRoleRow.from_input(data)
            db_session.add(user_role_row)
        return user_role_row.to_data()

    async def get_role(self, role_id: uuid.UUID) -> Optional[RoleData]:
        async with self._db.begin_readonly_session() as db_session:
            stmt = sa.select(RoleRow).where(RoleRow.id == role_id)
            result = await db_session.scalar(stmt)
            result = cast(Optional[RoleRow], result)
            if result is None:
                return None
            return result.to_data()

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
