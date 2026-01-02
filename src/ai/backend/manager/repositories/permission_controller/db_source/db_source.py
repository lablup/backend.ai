import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Optional, cast

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import contains_eager, selectinload

from ....data.permission.id import ObjectId, ScopeId
from ....data.permission.object_permission import (
    ObjectPermissionCreateInputBeforeRoleCreation,
)
from ....data.permission.permission import ScopedPermissionCreateInput
from ....data.permission.permission_group import (
    PermissionGroupCreator,
    PermissionGroupCreatorBeforeRoleCreation,
)
from ....data.permission.role import (
    AssignedUserData,
    AssignedUserListResult,
    RoleListResult,
    RolePermissionsUpdateInput,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ....data.permission.status import (
    RoleStatus,
)
from ....data.permission.types import OperationType, ScopeType
from ....errors.common import ObjectNotFound
from ....errors.permission import RoleAlreadyAssigned, RoleNotAssigned, RoleNotFound
from ....models.rbac_models.association_scopes_entities import AssociationScopesEntitiesRow
from ....models.rbac_models.permission.object_permission import ObjectPermissionRow
from ....models.rbac_models.permission.permission import PermissionRow
from ....models.rbac_models.permission.permission_group import PermissionGroupRow
from ....models.rbac_models.role import RoleRow
from ....models.rbac_models.user_role import UserRoleRow
from ....models.user import UserRow
from ....models.utils import ExtendedAsyncSAEngine
from ....repositories.base.creator import Creator, execute_creator
from ....repositories.base.purger import Purger, execute_purger
from ....repositories.base.querier import BatchQuerier, execute_batch_querier
from ....repositories.base.updater import Updater, execute_updater
from ..creators import (
    ObjectPermissionCreatorSpec,
    PermissionCreatorSpec,
    PermissionGroupCreatorSpec,
)


@dataclass
class CreateRoleInput:
    """Input for creating a role with permission groups and object permissions."""

    creator: Creator[RoleRow]
    permission_groups: Sequence[PermissionGroupCreatorBeforeRoleCreation]
    object_permissions: Sequence[ObjectPermissionCreateInputBeforeRoleCreation]


class PermissionDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def create_role(self, input_data: CreateRoleInput) -> RoleRow:
        """
        Create a new role with permission groups and object permissions.

        All related entities are created in a single transaction.

        Args:
            input_data: Input containing creator, permission groups, and object permissions

        Returns:
            Created role row
        """

        async with self._db.begin_session() as db_session:
            # 1. Create role
            result = await execute_creator(db_session, input_data.creator)
            role_row = result.row
            role_id = role_row.id

            # 2. Create permission groups with their nested permissions
            for group_input in input_data.permission_groups:
                group_creator_input = group_input.to_input(role_id)
                # 2-1. Create permission group
                group_creator = Creator(
                    spec=PermissionGroupCreatorSpec(
                        role_id=group_creator_input.role_id,
                        scope_id=group_creator_input.scope_id,
                        permissions=group_creator_input.permissions,
                    )
                )
                group_row = await self._add_permission_group(db_session, group_creator)

                # 2-2. Create nested permissions
                for perm_input in group_creator_input.permissions:
                    perm_creator = Creator(
                        spec=PermissionCreatorSpec(
                            permission_group_id=group_row.id,
                            entity_type=perm_input.entity_type,
                            operation=perm_input.operation,
                        )
                    )
                    await self._add_permission_to_group(db_session, perm_creator)

            # 3. Create object permissions
            for obj_perm_input in input_data.object_permissions:
                obj_perm_creator = Creator(
                    spec=ObjectPermissionCreatorSpec(
                        role_id=role_id,
                        entity_type=obj_perm_input.entity_type,
                        entity_id=obj_perm_input.entity_id,
                        operation=obj_perm_input.operation,
                        status=obj_perm_input.status,
                    )
                )
                await self._add_object_permission_to_role(db_session, obj_perm_creator)

            await db_session.refresh(role_row)
            return role_row

    async def create_permission_group(
        self,
        creator: Creator[PermissionGroupRow],
        permissions: Sequence[Creator[PermissionRow]] = tuple(),
    ) -> PermissionGroupRow:
        """
        Create a permission group with its nested permissions.

        All related entities are created in a single transaction.

        Args:
            creator: Permission group creator defining the group to create
            permissions: Optional sequence of permission creators to add to the group

        Returns:
            Created permission group row
        """
        async with self._db.begin_session() as db_session:
            # Create permission group
            pg_row = await self._add_permission_group(db_session, creator)

            # Create nested permissions
            for perm_creator in permissions:
                await self._add_permission_to_group(db_session, perm_creator)

            await db_session.refresh(pg_row)
            return pg_row

    async def create_permission(
        self,
        creator: Creator[PermissionRow],
    ) -> PermissionRow:
        """
        Create a permission in a permission group.

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

    async def delete_permission_group(
        self,
        purger: Purger[PermissionGroupRow],
    ) -> PermissionGroupRow | None:
        """
        Delete a permission group and its nested permissions (cascade).

        Args:
            purger: Purger with permission group ID

        Returns:
            Deleted permission group row, or None if not found
        """
        async with self._db.begin_session() as db_session:
            # Delete all permissions in this group first
            stmt_perms = sa.delete(PermissionRow).where(
                PermissionRow.permission_group_id == purger.pk_value
            )
            await db_session.execute(stmt_perms)

            # Delete the permission group
            result = await execute_purger(db_session, purger)
            return result.row if result else None

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
    ) -> Optional[ObjectPermissionRow]:
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
        result = cast(Optional[RoleRow], role_row)
        if result is None:
            raise ObjectNotFound(f"Role with ID {role_id} does not exist.")
        return result

    async def _find_permission_group_by_scope(
        self,
        db_session: SASession,
        role_id: uuid.UUID,
        scope_id: ScopeId,
    ) -> PermissionGroupRow | None:
        """
        Find permission group by role_id and scope.

        Used by update_role_permissions to find existing permission groups
        before adding permissions. If not found, a new permission group should
        be created.

        Args:
            db_session: Database session
            role_id: Role ID
            scope_id: Scope identifier (type + id)

        Returns:
            Permission group row if found, None otherwise
        """
        stmt = sa.select(PermissionGroupRow).where(
            PermissionGroupRow.role_id == role_id,
            PermissionGroupRow.scope_type == scope_id.scope_type,
            PermissionGroupRow.scope_id == scope_id.scope_id,
        )
        result = await db_session.scalar(stmt)
        return cast(Optional[PermissionGroupRow], result)

    async def _find_permission_groups_by_scopes(
        self,
        db_session: SASession,
        role_id: uuid.UUID,
        scope_ids: Sequence[ScopeId],
    ) -> dict[ScopeId, PermissionGroupRow]:
        """
        Find multiple permission groups by role_id and scopes in a single query.

        This is more efficient than calling _find_permission_group_by_scope
        multiple times when updating multiple scopes.

        Args:
            db_session: Database session
            role_id: Role ID
            scope_ids: List of scope identifiers to look up

        Returns:
            Dictionary mapping scope_id to permission group row (only existing groups)
        """
        if not scope_ids:
            return {}

        # Build OR conditions for all scopes
        scope_conditions = [
            sa.and_(
                PermissionGroupRow.scope_type == scope_id.scope_type,
                PermissionGroupRow.scope_id == scope_id.scope_id,
            )
            for scope_id in scope_ids
        ]

        stmt = sa.select(PermissionGroupRow).where(
            PermissionGroupRow.role_id == role_id,
            sa.or_(*scope_conditions),
        )

        result = await db_session.execute(stmt)
        pg_rows = result.scalars().all()

        # Build mapping: ScopeId -> PermissionGroupRow
        pg_map: dict[ScopeId, PermissionGroupRow] = {}
        for pg_row in pg_rows:
            scope_id = ScopeId(scope_type=pg_row.scope_type, scope_id=pg_row.scope_id)
            pg_map[scope_id] = pg_row

        return pg_map

    # ============================================================
    # Private Helper Functions (for use within transactions)
    # ============================================================

    async def _add_permission_group_to_role(
        self,
        db_session: SASession,
        pg_creator: PermissionGroupCreator,
    ) -> PermissionGroupRow:
        """Add a permission group with its permissions to a role (private, within transaction).

        Creates both the permission group and all its associated permissions
        in a single transaction.
        """

        # Create permission group with permissions list
        creator = Creator(
            spec=PermissionGroupCreatorSpec(
                role_id=pg_creator.role_id,
                scope_id=pg_creator.scope_id,
                permissions=pg_creator.permissions,
            )
        )
        result = await execute_creator(db_session, creator)
        pg_row = result.row

        # Create nested permissions
        for perm_input in pg_creator.permissions:
            perm_creator = Creator(
                spec=PermissionCreatorSpec(
                    permission_group_id=pg_row.id,
                    entity_type=perm_input.entity_type,
                    operation=perm_input.operation,
                )
            )
            await self._add_permission_to_group(db_session, perm_creator)

        return pg_row

    async def _remove_permission_group_from_role(
        self,
        db_session: SASession,
        purger: Purger[PermissionGroupRow],
    ) -> None:
        """Remove a permission group from a role (private, within transaction).

        Also deletes all permissions in this group.
        """
        # Delete all permissions in this group
        stmt_perms = sa.delete(PermissionRow).where(
            PermissionRow.permission_group_id == purger.pk_value
        )
        await db_session.execute(stmt_perms)

        # Delete the permission group using purger
        await execute_purger(db_session, purger)

    async def _add_permission_to_group(
        self,
        db_session: SASession,
        creator: Creator[PermissionRow],
    ) -> PermissionRow:
        """Add a permission to a permission group (private, within transaction)."""
        result = await execute_creator(db_session, creator)
        return result.row

    async def _remove_permission_from_group(
        self,
        db_session: SASession,
        purger: Purger[PermissionRow],
    ) -> None:
        """Remove a permission from a permission group (private, within transaction)."""
        await execute_purger(db_session, purger)

    async def _add_object_permission_to_role(
        self,
        db_session: SASession,
        creator: Creator[ObjectPermissionRow],
    ) -> ObjectPermissionRow:
        """Add an object permission to a role (private, within transaction)."""
        result = await execute_creator(db_session, creator)
        return result.row

    async def _add_permission_group(
        self,
        db_session: SASession,
        creator: Creator[PermissionGroupRow],
    ) -> PermissionGroupRow:
        """Add a permission group to a role (private, within transaction)."""
        result = await execute_creator(db_session, creator)
        return result.row

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
            user_role_row = UserRoleRow.from_input(data)
            try:
                db_session.add(user_role_row)  # type: ignore[arg-type]
                await db_session.flush()
                await db_session.refresh(user_role_row)
                return user_role_row
            except IntegrityError as e:
                raise RoleAlreadyAssigned(
                    f"Role {data.role_id} is already assigned to user {data.user_id}."
                ) from e

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
        Update role permissions in batch using scope-based management.

        For scoped permissions:
        - Automatically finds or creates permission groups by (role_id, scope_type, scope_id)
        - Groups permissions by scope to minimize database lookups
        - All operations are performed in a single transaction

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
            # Group by scope to minimize permission group lookups
            scoped_perms_by_scope: dict[ScopeId, list[ScopedPermissionCreateInput]] = {}
            for scoped_perm_input in input_data.add_scoped_permissions:
                scope_id = scoped_perm_input.to_scope_id()
                if scope_id not in scoped_perms_by_scope:
                    scoped_perms_by_scope[scope_id] = []
                scoped_perms_by_scope[scope_id].append(scoped_perm_input)

            # Bulk fetch all permission groups for the scopes (performance optimization)
            pg_map = await self._find_permission_groups_by_scopes(
                db_session,
                role_id=input_data.role_id,
                scope_ids=list(scoped_perms_by_scope.keys()),
            )

            # For each scope, find or create permission group and add permissions
            for scope_id, perm_inputs in scoped_perms_by_scope.items():
                # Get existing permission group from bulk result
                pg_row = pg_map.get(scope_id)

                # Create permission group if not exists
                if pg_row is None:
                    pg_creator = Creator(
                        spec=PermissionGroupCreatorSpec(
                            role_id=input_data.role_id,
                            scope_id=scope_id,
                        )
                    )
                    pg_row = await self._add_permission_group(db_session, pg_creator)

                # Add permissions to the permission group
                for perm_input in perm_inputs:
                    perm_creator = Creator(
                        spec=PermissionCreatorSpec(
                            permission_group_id=pg_row.id,
                            entity_type=perm_input.entity_type,
                            operation=perm_input.operation,
                        )
                    )
                    await self._add_permission_to_group(db_session, perm_creator)

            # 2. Remove scoped permissions
            for perm_id in input_data.remove_scoped_permission_ids:
                perm_purger = Purger(row_class=PermissionRow, pk_value=perm_id)
                await self._remove_permission_from_group(db_session, perm_purger)

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

    async def check_scope_permission_exist(
        self,
        user_id: uuid.UUID,
        scope_id: ScopeId,
        operation: OperationType,
    ) -> bool:
        role_query = (
            sa.select(sa.func.exist())
            .select_from(
                sa.join(UserRoleRow, RoleRow.id == UserRoleRow.role_id)
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
            .options(
                contains_eager(RoleRow.permission_group_rows).options(
                    selectinload(PermissionGroupRow.permission_rows)
                )
            )
        )
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

    async def search_roles(
        self,
        querier: BatchQuerier,
    ) -> RoleListResult:
        """Searches roles with pagination and filtering.

        Uses LEFT JOIN with PermissionGroupRow and ObjectPermissionRow to support
        scope-based and entity-based filtering. The JOINs are always performed to
        simplify the implementation, with distinct() used to prevent duplicates.
        """
        async with self._db.begin_readonly_session() as db_sess:
            # Build query with LEFT JOINs to support scope and entity filtering
            query = (
                sa.select(RoleRow)
                .outerjoin(
                    PermissionGroupRow,
                    RoleRow.id == PermissionGroupRow.role_id,
                )
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

    async def get_role_with_permissions(self, role_id: uuid.UUID) -> RoleRow:
        """Get role with eagerly loaded permissions only (no users)."""
        async with self._db.begin_readonly_session() as db_sess:
            stmt = (
                sa.select(RoleRow)
                .where(RoleRow.id == role_id)
                .options(
                    selectinload(RoleRow.permission_group_rows).selectinload(
                        PermissionGroupRow.permission_rows
                    ),
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
                    user_id=row.UserRow.uuid,
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
