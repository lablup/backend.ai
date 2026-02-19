import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import contains_eager, selectinload

from ai.backend.manager.data.permission.entity import (
    EntityData,
    EntityListResult,
    EntityRefListResult,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.object_permission import (
    ObjectPermissionCreateInputBeforeRoleCreation,
    ObjectPermissionListResult,
)
from ai.backend.manager.data.permission.permission import (
    PermissionListResult,
)
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    AssignedUserListResult,
    RoleListResult,
    RolePermissionsUpdateInput,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.status import (
    RoleStatus,
)
from ai.backend.manager.data.permission.types import (
    OperationType,
    ScopeData,
    ScopeListResult,
    ScopeType,
)
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.permission import RoleNotAssigned, RoleNotFound
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.permission_controller.creators import (
    ObjectPermissionCreatorSpec,
    PermissionCreatorSpec,
    UserRoleCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.types import (
    ObjectPermissionSearchScope,
    PermissionSearchScope,
)


@dataclass
class CreateRoleInput:
    """Input for creating a role with object permissions."""

    creator: Creator[RoleRow]
    object_permissions: Sequence[ObjectPermissionCreateInputBeforeRoleCreation]


class PermissionDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create_role(self, input_data: CreateRoleInput) -> RoleRow:
        """
        Create a new role with object permissions.

        All related entities are created in a single transaction.

        Args:
            input_data: Input containing creator and object permissions

        Returns:
            Created role row
        """
        async with self._db.begin_session() as db_session:
            # 1. Create role
            result = await execute_creator(db_session, input_data.creator)
            role_row = result.row

            await db_session.refresh(role_row)
            return role_row

    async def create_permission(
        self,
        creator: Creator[PermissionRow],
    ) -> PermissionRow:
        """
        Create a permission.

        Args:
            creator: Permission creator defining the permission to create

        Returns:
            Created permission row
        """
        async with self._db.begin_session() as db_session:
            perm_row = await self._add_permission_to_group(db_session, creator)
            await db_session.refresh(perm_row)
            return perm_row

    async def create_object_permission(
        self,
        creator: Creator[ObjectPermissionRow],
    ) -> ObjectPermissionRow:
        """
        Create an object permission for a role.

        Args:
            creator: Object permission creator defining the permission to create

        Returns:
            Created object permission row
        """
        async with self._db.begin_session() as db_session:
            obj_perm_row = await self._add_object_permission_to_role(db_session, creator)
            await db_session.refresh(obj_perm_row)
            return obj_perm_row

    async def delete_permission(
        self,
        purger: Purger[PermissionRow],
    ) -> PermissionRow:
        """
        Delete a permission.

        Args:
            purger: Purger with permission ID

        Returns:
            Deleted permission row

        Raises:
            ObjectNotFound: If permission does not exist
        """
        async with self._db.begin_session() as db_session:
            result = await execute_purger(db_session, purger)
            if result is None:
                raise ObjectNotFound(f"Permission with ID {purger.pk_value} does not exist.")
            return result.row

    async def delete_object_permission(
        self,
        purger: Purger[ObjectPermissionRow],
    ) -> ObjectPermissionRow | None:
        """
        Delete an object permission.

        Args:
            purger: Purger with object permission ID

        Returns:
            Deleted object permission row, or None if not found
        """
        async with self._db.begin_session() as db_session:
            result = await execute_purger(db_session, purger)
            return result.row if result else None

    async def _get_role(self, db_session: SASession, role_id: uuid.UUID) -> RoleRow:
        stmt = sa.select(RoleRow).where(RoleRow.id == role_id)
        role_row = await db_session.scalar(stmt)
        result = role_row
        if result is None:
            raise ObjectNotFound(f"Role with ID {role_id} does not exist.")
        return result

    # ============================================================
    # Private Helper Functions (for use within transactions)
    # ============================================================

    async def _add_permission_to_group(
        self,
        db_session: SASession,
        creator: Creator[PermissionRow],
    ) -> PermissionRow:
        """Add a permission (private, within transaction)."""
        result = await execute_creator(db_session, creator)
        return result.row

    async def _add_object_permission_to_role(
        self,
        db_session: SASession,
        creator: Creator[ObjectPermissionRow],
    ) -> ObjectPermissionRow:
        """Add an object permission to a role (private, within transaction)."""
        result = await execute_creator(db_session, creator)
        return result.row

    async def _remove_permission(
        self,
        db_session: SASession,
        purger: Purger[PermissionRow],
    ) -> None:
        """Remove a permission (private, within transaction)."""
        await execute_purger(db_session, purger)

    async def _remove_object_permission_from_role(
        self,
        db_session: SASession,
        purger: Purger[ObjectPermissionRow],
    ) -> None:
        """Remove an object permission from a role (private, within transaction)."""
        await execute_purger(db_session, purger)

    async def update_role(self, updater: Updater[RoleRow]) -> RoleRow:
        async with self._db.begin_session() as db_session:
            result = await execute_updater(db_session, updater)
            if result is None:
                raise ObjectNotFound(f"Role with ID {updater.pk_value} does not exist.")
            return result.row

    async def delete_role(self, updater: Updater[RoleRow]) -> RoleRow:
        async with self._db.begin_session() as db_session:
            result = await execute_updater(db_session, updater)
            if result is None:
                raise ObjectNotFound(f"Role with ID {updater.pk_value} does not exist.")
            return result.row

    async def purge_role(self, purger: Purger[RoleRow]) -> RoleRow:
        async with self._db.begin_session() as db_session:
            result = await execute_purger(db_session, purger)
            if result is None:
                raise ObjectNotFound(f"Role with ID {purger.pk_value} does not exist.")
            return result.row

    async def assign_role(self, data: UserRoleAssignmentInput) -> UserRoleRow:
        async with self._db.begin_session() as db_session:
            creator = Creator(
                spec=UserRoleCreatorSpec(
                    user_id=data.user_id,
                    role_id=data.role_id,
                    granted_by=data.granted_by,
                )
            )
            result = await execute_creator(db_session, creator)
            return result.row

    async def revoke_role(self, data: UserRoleRevocationInput) -> uuid.UUID:
        async with self._db.begin_session() as db_session:
            stmt = (
                sa.select(UserRoleRow)
                .where(UserRoleRow.user_id == data.user_id)
                .where(UserRoleRow.role_id == data.role_id)
            )
            user_role_row = await db_session.scalar(stmt)

            if user_role_row is None:
                raise RoleNotAssigned(
                    f"Role {data.role_id} is not assigned to user {data.user_id}."
                )

            user_role_id = user_role_row.id
            await db_session.delete(user_role_row)
            await db_session.flush()
            return user_role_id

    async def update_role_permissions(
        self,
        input_data: RolePermissionsUpdateInput,
    ) -> RoleRow:
        """
        Update role permissions in batch.

        Args:
            input_data: Batch update input containing scoped and object permissions

        Returns:
            Updated role with refreshed relationships

        Raises:
            ObjectNotFound: If role does not exist
        """
        async with self._db.begin_session() as db_session:
            # 0. Verify role exists
            role_row = await self._get_role(db_session, input_data.role_id)

            # 1. Add scoped permissions
            for scoped_perm_input in input_data.add_scoped_permissions:
                perm_creator = Creator(
                    spec=PermissionCreatorSpec(
                        role_id=input_data.role_id,
                        scope_type=scoped_perm_input.scope_type,
                        scope_id=scoped_perm_input.scope_id,
                        entity_type=scoped_perm_input.entity_type,
                        operation=scoped_perm_input.operation,
                    )
                )
                await self._add_permission_to_group(db_session, perm_creator)

            # 2. Remove scoped permissions
            for perm_id in input_data.remove_scoped_permission_ids:
                perm_purger = Purger(row_class=PermissionRow, pk_value=perm_id)
                await self._remove_permission(db_session, perm_purger)

            # 3. Add object permissions
            for obj_perm_input in input_data.add_object_permissions:
                obj_perm_creator = Creator(
                    spec=ObjectPermissionCreatorSpec(
                        role_id=input_data.role_id,
                        entity_type=obj_perm_input.entity_type,
                        entity_id=obj_perm_input.entity_id,
                        operation=obj_perm_input.operation,
                        status=obj_perm_input.status,
                    )
                )
                await self._add_object_permission_to_role(db_session, obj_perm_creator)

            # 4. Remove object permissions
            for obj_perm_id in input_data.remove_object_permission_ids:
                obj_perm_purger = Purger(row_class=ObjectPermissionRow, pk_value=obj_perm_id)
                await self._remove_object_permission_from_role(db_session, obj_perm_purger)

            # 5. Refresh and return
            await db_session.refresh(role_row)
            return role_row

    async def get_role(self, role_id: uuid.UUID) -> RoleRow | None:
        async with self._db.begin_readonly_session_read_committed() as db_session:
            try:
                result = await self._get_role(db_session, role_id)
            except ObjectNotFound:
                return None
            return result

    async def get_user_roles(self, user_id: uuid.UUID) -> list[RoleRow]:
        async with self._db.begin_readonly_session_read_committed() as db_session:
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
                    PermissionRow,
                    RoleRow.id == PermissionRow.role_id,
                )
            )
            stmt = (
                sa.select(RoleRow)
                .select_from(j)
                .where(UserRoleRow.user_id == user_id)
                .options(
                    selectinload(RoleRow.object_permission_rows),
                )
            )

            result = await db_session.scalars(stmt)
            return list(result.all())

    async def get_entity_mapped_scopes(
        self, target_object_id: ObjectId
    ) -> list[AssociationScopesEntitiesRow]:
        async with self._db.begin_readonly_session_read_committed() as db_session:
            stmt = sa.select(AssociationScopesEntitiesRow).where(
                AssociationScopesEntitiesRow.entity_id == target_object_id.entity_id,
                AssociationScopesEntitiesRow.entity_type == target_object_id.entity_type.value,
            )
            result = await db_session.scalars(stmt)
            return list(result.all())

    async def check_scope_permission_exist(
        self,
        user_id: uuid.UUID,
        scope_id: ScopeId,
        operation: OperationType,
    ) -> bool:
        role_query = (
            sa.select(sa.func.exist())
            .select_from(
                sa.join(RoleRow, UserRoleRow, RoleRow.id == UserRoleRow.role_id).join(
                    PermissionRow, RoleRow.id == PermissionRow.role_id
                )
            )
            .where(
                sa.and_(
                    RoleRow.status == RoleStatus.ACTIVE,
                    UserRoleRow.user_id == user_id,
                    sa.or_(
                        PermissionRow.scope_type == ScopeType.GLOBAL,
                        PermissionRow.scope_id == scope_id.scope_id,
                    ),
                    PermissionRow.operation == operation,
                )
            )
        )
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.scalar(role_query)
            return result or False

    def _make_query_statement_for_object_permission(
        self,
        user_id: uuid.UUID,
        object_ids: Iterable[ObjectId],
    ) -> sa.sql.Select[Any]:
        object_id_for_cond = [obj_id.entity_id for obj_id in object_ids]
        return (
            sa.select(RoleRow)
            .select_from(
                sa.join(RoleRow, UserRoleRow, RoleRow.id == UserRoleRow.role_id)
                .join(PermissionRow, RoleRow.id == PermissionRow.role_id)
                .join(
                    AssociationScopesEntitiesRow,
                    sa.and_(
                        PermissionRow.scope_id == AssociationScopesEntitiesRow.scope_id,
                        PermissionRow.scope_type == AssociationScopesEntitiesRow.scope_type,
                    ),
                )
                .join(ObjectPermissionRow, RoleRow.id == ObjectPermissionRow.role_id)
            )
            .where(
                sa.and_(
                    RoleRow.status == RoleStatus.ACTIVE,
                    UserRoleRow.user_id == user_id,
                    sa.or_(
                        PermissionRow.scope_type == ScopeType.GLOBAL,
                        AssociationScopesEntitiesRow.entity_id.in_(object_id_for_cond),
                        ObjectPermissionRow.entity_id.in_(object_id_for_cond),
                    ),
                )
            )
            .options(
                contains_eager(RoleRow.object_permission_rows),
            )
        )

    def _make_query_statement_for_object_permissions(
        self,
        user_id: uuid.UUID,
        object_ids: Iterable[ObjectId],
        operation: OperationType,
    ) -> sa.sql.Select[Any]:
        object_id_for_cond = [obj_id.entity_id for obj_id in object_ids]
        return (
            sa.select(RoleRow)
            .select_from(
                sa.join(RoleRow, UserRoleRow, RoleRow.id == UserRoleRow.role_id)
                .join(PermissionRow, RoleRow.id == PermissionRow.role_id)
                .join(
                    AssociationScopesEntitiesRow,
                    sa.and_(
                        PermissionRow.scope_id == AssociationScopesEntitiesRow.scope_id,
                        PermissionRow.scope_type == AssociationScopesEntitiesRow.scope_type,
                    ),
                )
                .join(ObjectPermissionRow, RoleRow.id == ObjectPermissionRow.role_id)
            )
            .where(
                sa.and_(
                    RoleRow.status == RoleStatus.ACTIVE,
                    UserRoleRow.user_id == user_id,
                    sa.or_(
                        sa.and_(
                            PermissionRow.scope_type == ScopeType.GLOBAL,
                            PermissionRow.operation == operation,
                        ),
                        sa.and_(
                            AssociationScopesEntitiesRow.entity_id.in_(object_id_for_cond),
                            PermissionRow.operation == operation,
                        ),
                        sa.and_(
                            ObjectPermissionRow.entity_id.in_(object_id_for_cond),
                            ObjectPermissionRow.operation == operation,
                        ),
                    ),
                )
            )
            .options(
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
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.scalars(role_query)
            role_rows = cast(list[RoleRow], result.all())
            return len(role_rows) > 0

    async def check_batch_object_permission_exist(
        self,
        user_id: uuid.UUID,
        object_ids: Iterable[ObjectId],
        operation: OperationType,
    ) -> dict[ObjectId, bool]:
        result: dict[ObjectId, bool] = dict.fromkeys(object_ids, False)
        role_query = self._make_query_statement_for_object_permissions(
            user_id, object_ids, operation
        )
        async with self._db.begin_readonly_session_read_committed() as db_session:
            role_rows_result = await db_session.scalars(role_query)
            role_rows = list(role_rows_result.all())

            for role in role_rows:
                for op in role.object_permission_rows:
                    object_id = op.object_id()
                    result[object_id] = True
        return result

    async def search_roles(
        self,
        querier: BatchQuerier,
    ) -> RoleListResult:
        """Searches roles with pagination and filtering.

        Uses LEFT JOIN with ObjectPermissionRow to support
        entity-based filtering. The JOIN is always performed to
        simplify the implementation, with distinct() used to prevent duplicates.
        """
        async with self._db.begin_readonly_session() as db_sess:
            # Build query with LEFT JOIN to support entity filtering
            query = (
                sa.select(RoleRow)
                .outerjoin(
                    ObjectPermissionRow,
                    RoleRow.id == ObjectPermissionRow.role_id,
                )
                .distinct()
            )

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.RoleRow.to_data() for row in result.rows]

            return RoleListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_permissions(
        self,
        querier: BatchQuerier,
        scope: PermissionSearchScope | None = None,
    ) -> PermissionListResult:
        """Searches permissions with pagination and filtering."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(PermissionRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
                scope,
            )

            items = [row.PermissionRow.to_data() for row in result.rows]

            return PermissionListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_object_permissions(
        self,
        querier: BatchQuerier,
        scope: ObjectPermissionSearchScope | None = None,
    ) -> ObjectPermissionListResult:
        """Searches object permissions with pagination and filtering."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ObjectPermissionRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
                scope,
            )

            items = [row.ObjectPermissionRow.to_data() for row in result.rows]

            return ObjectPermissionListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def get_role_with_permissions(self, role_id: uuid.UUID) -> RoleRow:
        """Get role with eagerly loaded permissions only (no users)."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = (
                sa.select(RoleRow)
                .where(RoleRow.id == role_id)
                .options(
                    selectinload(RoleRow.object_permission_rows),
                )
            )
            result = await db_sess.execute(stmt)
            role_row = result.scalar_one_or_none()
            if role_row is None:
                raise RoleNotFound(f"Role with ID {role_id} does not exist.")
            return role_row

    async def search_users_assigned_to_role(
        self,
        querier: BatchQuerier,
    ) -> AssignedUserListResult:
        """Searches users assigned to a specific role with pagination and filtering."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(UserRow, UserRoleRow).select_from(
                sa.join(
                    UserRow,
                    UserRoleRow,
                    UserRoleRow.user_id == UserRow.uuid,
                )
            )
            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [
                AssignedUserData(
                    id=row.UserRoleRow.id,
                    user_id=row.UserRow.uuid,
                    role_id=row.UserRoleRow.role_id,
                    granted_by=row.UserRoleRow.granted_by,
                    granted_at=row.UserRoleRow.granted_at,
                )
                for row in result.rows
            ]

            return AssignedUserListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_domain_scopes(
        self,
        querier: BatchQuerier,
    ) -> ScopeListResult:
        """Search all domains using BatchQuerier."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(DomainRow.name)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [
                ScopeData(
                    id=ScopeId(scope_type=ScopeType.DOMAIN, scope_id=row.name),
                    name=row.name,
                )
                for row in result.rows
            ]

            return ScopeListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_project_scopes(
        self,
        querier: BatchQuerier,
    ) -> ScopeListResult:
        """Search all projects using BatchQuerier."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(GroupRow.id, GroupRow.name)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [
                ScopeData(
                    id=ScopeId(scope_type=ScopeType.PROJECT, scope_id=str(row.id)),
                    name=row.name,
                )
                for row in result.rows
            ]

            return ScopeListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_user_scopes(
        self,
        querier: BatchQuerier,
    ) -> ScopeListResult:
        """Search all users using BatchQuerier."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(UserRow.uuid, UserRow.username, UserRow.email)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [
                ScopeData(
                    id=ScopeId(scope_type=ScopeType.USER, scope_id=str(row.uuid)),
                    name=row.username if row.username is not None else row.email,
                )
                for row in result.rows
            ]

            return ScopeListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_entities_in_scope(
        self,
        querier: BatchQuerier,
    ) -> EntityListResult:
        """Search entities within a scope."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(
                AssociationScopesEntitiesRow.entity_id,
                AssociationScopesEntitiesRow.entity_type,
            )

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [
                EntityData(
                    entity_type=row.entity_type,
                    entity_id=row.entity_id,
                )
                for row in result.rows
            ]

            return EntityListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_entity_refs_in_scope(
        self,
        querier: BatchQuerier,
    ) -> EntityRefListResult:
        """Search entity refs (full association rows) within a scope."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AssociationScopesEntitiesRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.AssociationScopesEntitiesRow.to_data() for row in result.rows]

            return EntityRefListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
