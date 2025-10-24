import uuid
from collections.abc import Iterable
from typing import Optional, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import contains_eager, selectinload

from ...data.permission.id import ObjectId, ScopeId
from ...data.permission.role import (
    RoleCreateInput,
    RoleDeleteInput,
    RoleUpdateInput,
    UserRoleAssignmentInput,
)
from ...data.permission.status import (
    RoleStatus,
)
from ...data.permission.types import OperationType, ScopeType
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

    async def check_scope_permission_exist(
        self,
        user_id: uuid.UUID,
        scope_id: ScopeId,
        operation: OperationType,
    ) -> bool:
        exist_query = sa.exists(
            sa.select(1)
            .select_from(
                sa.join(UserRoleRow, RoleRow, RoleRow.id == UserRoleRow.role_id)
                .join(PermissionGroupRow, RoleRow.id == PermissionGroupRow.role_id)
                .join(PermissionRow, PermissionGroupRow.id == PermissionRow.permission_group_id)
            )
            .where(
                sa.and_(
                    RoleRow.status == RoleStatus.ACTIVE,
                    UserRoleRow.user_id == user_id,
                    sa.or_(
                        PermissionGroupRow.scope_type == ScopeType.GLOBAL,
                        PermissionGroupRow.scope_id == scope_id.scope_id,
                    ),
                    PermissionRow.operation == operation,
                )
            )
        )
        role_query = sa.select(exist_query)
        async with self._db.begin_readonly_session() as db_session:
            result = await db_session.scalar(role_query)
            return result

    def _make_query_statement_for_object_permission(
        self,
        user_id: uuid.UUID,
        object_ids: Iterable[ObjectId],
    ) -> sa.sql.Select:
        object_id_for_cond = [obj_id.entity_id for obj_id in object_ids]
        return (
            sa.select(RoleRow)
            .select_from(
                sa.join(UserRoleRow, RoleRow.id == UserRoleRow.role_id)
                .join(PermissionGroupRow, RoleRow.id == PermissionGroupRow.role_id)
                .join(
                    AssociationScopesEntitiesRow,
                    PermissionGroupRow.scope_id == AssociationScopesEntitiesRow.scope_id,
                )
                .join(ObjectPermissionRow, RoleRow.id == ObjectPermissionRow.role_id)
            )
            .where(
                sa.and_(
                    RoleRow.status == RoleStatus.ACTIVE,
                    UserRoleRow.user_id == user_id,
                    sa.or_(
                        PermissionGroupRow.scope_type == ScopeType.GLOBAL,
                        AssociationScopesEntitiesRow.entity_id.in_(object_id_for_cond),  # type: ignore[attr-defined]
                        ObjectPermissionRow.entity_id.in_(object_id_for_cond),  # type: ignore[attr-defined]
                    ),
                )
            )
            .options(
                contains_eager(RoleRow.permission_group_rows).options(
                    contains_eager(PermissionGroupRow.mapped_entities),
                    selectinload(PermissionGroupRow.permission_rows),
                ),
                contains_eager(RoleRow.object_permission_rows),
            )
        )

    def _make_query_statement_for_object_permissions(
        self,
        user_id: uuid.UUID,
        object_ids: Iterable[ObjectId],
        operation: OperationType,
    ) -> sa.sql.Select:
        object_id_for_cond = [obj_id.entity_id for obj_id in object_ids]
        return (
            sa.select(RoleRow)
            .select_from(
                sa.join(UserRoleRow, RoleRow.id == UserRoleRow.role_id)
                .join(PermissionGroupRow, RoleRow.id == PermissionGroupRow.role_id)
                .join(
                    AssociationScopesEntitiesRow,
                    PermissionGroupRow.scope_id == AssociationScopesEntitiesRow.scope_id,
                )
                .join(PermissionRow, PermissionGroupRow.id == PermissionRow.permission_group_id)
                .join(ObjectPermissionRow, RoleRow.id == ObjectPermissionRow.role_id)
            )
            .where(
                sa.and_(
                    RoleRow.status == RoleStatus.ACTIVE,
                    UserRoleRow.user_id == user_id,
                    sa.or_(
                        sa.and_(
                            PermissionGroupRow.scope_type == ScopeType.GLOBAL,
                            PermissionRow.operation == operation,
                        ),
                        sa.and_(
                            AssociationScopesEntitiesRow.entity_id.in_(object_id_for_cond),  # type: ignore[attr-defined]
                            PermissionRow.operation == operation,
                        ),
                        sa.and_(
                            ObjectPermissionRow.entity_id.in_(object_id_for_cond),  # type: ignore[attr-defined]
                            ObjectPermissionRow.operation == operation,
                        ),
                    ),
                )
            )
            .options(
                contains_eager(RoleRow.permission_group_rows).options(
                    contains_eager(PermissionGroupRow.mapped_entities),
                    contains_eager(PermissionGroupRow.permission_rows),
                ),
                contains_eager(RoleRow.object_permission_rows),
            )
        )

    async def check_object_permission_exist(
        self,
        user_id: uuid.UUID,
        object_id: ObjectId,
        operation: OperationType,
    ) -> bool:
        role_query = self._make_query_statement_for_object_permissions(
            user_id, [object_id], operation
        )
        async with self._db.begin_readonly_session() as db_session:
            result = await db_session.scalars(role_query)
            role_rows = cast(list[RoleRow], result.all())
            return len(role_rows) > 0

    async def check_batch_object_permission_exist(
        self,
        user_id: uuid.UUID,
        object_ids: Iterable[ObjectId],
        operation: OperationType,
    ) -> dict[ObjectId, bool]:
        result: dict[ObjectId, bool] = {object_id: False for object_id in object_ids}
        role_query = self._make_query_statement_for_object_permissions(
            user_id, object_ids, operation
        )
        async with self._db.begin_readonly_session() as db_session:
            role_rows = await db_session.scalars(role_query)
            role_rows = cast(list[RoleRow], role_rows.all())

            for role in role_rows:
                for op in role.object_permission_rows:
                    object_id = op.object_id()
                    result[object_id] = True
                for pg in role.permission_group_rows:
                    if pg.scope_type == ScopeType.GLOBAL:
                        return {obj_id: True for obj_id in object_ids}
                    else:
                        for object in pg.mapped_entities:
                            object_id = object.object_id()
                            result[object_id] = True
        return result
