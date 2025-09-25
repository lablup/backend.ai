import uuid
from typing import Optional, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import contains_eager

from ...data.permission.id import ObjectId
from ...data.permission.role import (
    RoleCreateInput,
    RoleDeleteInput,
    RoleUpdateInput,
    UserRoleAssignmentInput,
)
from ...data.permission.status import (
    RoleStatus,
)
from ...errors.common import ObjectNotFound
from ...models.rbac_models.association_scopes_entities import AssociationScopesEntitiesRow
from ...models.rbac_models.permission.object_permission import ObjectPermissionRow
from ...models.rbac_models.permission.permission import PermissionRow
from ...models.rbac_models.permission.permission_group import PermissionGroupRow
from ...models.rbac_models.role import RoleRow
from ...models.rbac_models.user_role import UserRoleRow
from ...models.utils import ExtendedAsyncSAEngine


class PermissionDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create_role(self, data: RoleCreateInput) -> RoleRow:
        """
        Create a new role in the database.

        Returns the ID of the created role.
        """
        async with self._db.begin_session() as db_session:
            role_row = RoleRow.from_input(data)
            db_session.add(role_row)  # type: ignore[arg-type]
            await db_session.flush()
            role_id = role_row.id
            for permission_group in data.permission_groups:
                permission_group_row = PermissionGroupRow.from_input(
                    permission_group.to_input(role_id)
                )
                db_session.add(permission_group_row)  # type: ignore[arg-type]
            for object_permission in data.object_permissions:
                object_permission_row = ObjectPermissionRow.from_input(
                    object_permission.to_input(role_id)
                )
                db_session.add(object_permission_row)  # type: ignore[arg-type]
            await db_session.flush()
            await db_session.refresh(role_row)
            return role_row

    async def _get_role(self, db_session: SASession, role_id: uuid.UUID) -> RoleRow:
        stmt = sa.select(RoleRow).where(RoleRow.id == role_id)
        role_row = await db_session.scalar(stmt)
        result = cast(Optional[RoleRow], role_row)
        if result is None:
            raise ObjectNotFound(f"Role with ID {role_id} does not exist.")
        return result

    async def update_role(self, data: RoleUpdateInput) -> RoleRow:
        to_update = data.fields_to_update()
        async with self._db.begin_session() as db_session:
            stmt = sa.update(RoleRow).where(RoleRow.id == data.id).values(**to_update)
            await db_session.execute(stmt)
            role_row = await self._get_role(db_session, data.id)
            return role_row

    async def delete_role(self, data: RoleDeleteInput) -> RoleRow:
        async with self._db.begin_session() as db_session:
            role_row = await self._get_role(db_session, data.id)
            role_row.status = RoleStatus.DELETED
            await db_session.flush()
            await db_session.refresh(role_row)
            return role_row

    async def assign_role(self, data: UserRoleAssignmentInput) -> UserRoleRow:
        async with self._db.begin_session() as db_session:
            user_role_row = UserRoleRow.from_input(data)
            db_session.add(user_role_row)  # type: ignore[arg-type]
            await db_session.flush()
            await db_session.refresh(user_role_row)
            return user_role_row

    async def get_role(self, role_id: uuid.UUID) -> Optional[RoleRow]:
        async with self._db.begin_readonly_session() as db_session:
            try:
                result = await self._get_role(db_session, role_id)
            except ObjectNotFound:
                return None
            return result

    async def get_user_roles(self, user_id: uuid.UUID) -> list[RoleRow]:
        async with self._db.begin_readonly_session() as db_session:
            j = (
                sa.join(
                    RoleRow,
                    UserRoleRow,
                    RoleRow.id == UserRoleRow.role_id,
                )
                .join(
                    ObjectPermissionRow,
                    RoleRow.id == ObjectPermissionRow.role_id,
                )
                .join(
                    PermissionGroupRow,
                    RoleRow.id == PermissionGroupRow.role_id,
                )
                .join(
                    PermissionRow,
                    PermissionGroupRow.id == PermissionRow.permission_group_id,
                )
            )
            stmt = (
                sa.select(RoleRow)
                .select_from(j)
                .where(UserRoleRow.user_id == user_id)
                .options(
                    contains_eager(RoleRow.permission_group_rows).options(
                        contains_eager(PermissionGroupRow.permission_rows)
                    ),
                    contains_eager(RoleRow.object_permission_rows),
                )
            )

            result = await db_session.scalars(stmt)
            return result.all()

    async def get_entity_mapped_scopes(
        self, target_object_id: ObjectId
    ) -> list[AssociationScopesEntitiesRow]:
        async with self._db.begin_readonly_session() as db_session:
            stmt = sa.select(AssociationScopesEntitiesRow.scope_id).where(
                AssociationScopesEntitiesRow.entity_id == target_object_id.entity_id,
                AssociationScopesEntitiesRow.entity_type == target_object_id.entity_type.value,
            )
            result = await db_session.scalars(stmt)
            return result.all()
