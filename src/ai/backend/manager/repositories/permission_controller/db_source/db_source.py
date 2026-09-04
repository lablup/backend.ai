import logging
import uuid
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import contains_eager, selectinload

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import (
    RBACElementType,
    RelationType,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.permission.entity import (
    ElementAssociationListResult,
    EntityData,
    EntityListResult,
)
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.object_permission import (
    ObjectPermissionCreateInputBeforeRoleCreation,
)
from ai.backend.manager.data.permission.permission import (
    PermissionListResult,
)
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    AssignedUserListResult,
    BulkPermissionCheckInput,
    BulkRoleRevocationFailure,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
    PermissionResolutionKey,
    ProjectRoleCount,
    RoleListResult,
    RolePermissionsUpdateInput,
    RoleRevocationResult,
    ScopeChainPermissionCheckInput,
    UserRoleAssignmentInput,
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.status import (
    RoleStatus,
)
from ai.backend.manager.data.permission.types import (
    EntityType as LegacyEntityType,
)
from ai.backend.manager.data.permission.types import (
    OperationType,
    Permission,
    RBACElementRef,
    ScopeData,
    ScopeListResult,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as LegacyScopeType,
)
from ai.backend.manager.data.permission.virtual_entity import (
    GovernCheckKey,
    OwnCheckKey,
)
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.permission import RoleNotAssigned, RoleNotFound
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.scopes import PermissionOperationScope
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.scopes import ScopedRoleOperationScope
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    BulkCreatorResultWithFailures,
    Creator,
    execute_bulk_creator_partial,
    execute_creator,
)
from ai.backend.manager.repositories.base.purger import (
    BulkPurgerResultWithFailures,
    Purger,
    execute_bulk_purger_partial,
    execute_purger,
)
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.updater import Updater, execute_updater
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.permission_controller.creators import (
    ObjectPermissionCreatorSpec,
    PermissionCreatorSpec,
    UserRoleCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.purgers import (
    ObjectPermissionPurgerSpec,
    PermissionPurgerSpec,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class CreateRoleInput:
    """Input for creating a role with object permissions."""

    creator: Creator[RoleRow]
    object_permissions: Sequence[ObjectPermissionCreateInputBeforeRoleCreation]
    scope_refs: Sequence[RBACElementRef] = field(default_factory=list)


@dataclass(frozen=True)
class _PermissionGroupKey:
    """Group key for batching ``PermissionResolutionKey`` inputs.

    Keys sharing the same ``(user_id, element_type, subject_entity_type)`` are
    resolved by a single SQL round-trip differing only in the per-row
    ``entity_id`` IN-list.
    """

    user_id: uuid.UUID
    element_type: RBACElementType
    subject_entity_type: RBACElementType


class PermissionDBSource:
    _db: ExtendedAsyncSAEngine
    _ops: PermissionOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._ops = PermissionOpsProvider(db)

    # ------------------------------------------------------------------ role CRUD

    async def create_role(self, input_data: CreateRoleInput) -> RoleRow:
        """
        Create a new role with object permissions.

        All related entities are created in a single transaction.
        When scope_refs is non-empty, the role is also registered in
        association_scopes_entities via RBACEntityCreator.

        Args:
            input_data: Input containing creator and object permissions

        Returns:
            Created role row
        """
        async with self._db.begin_session() as db_session:
            if input_data.scope_refs:
                rbac_creator = RBACEntityCreator(
                    spec=input_data.creator.spec,
                    element_type=RBACElementType.ROLE,
                    scope_ref=input_data.scope_refs[0],
                    additional_scope_refs=input_data.scope_refs[1:],
                )
                role_row = (await execute_rbac_entity_creator(db_session, rbac_creator)).row
            else:
                role_row = (await execute_creator(db_session, input_data.creator)).row

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
                raise ObjectNotFound(f"Permission with ID {purger.spec.pk_value()} does not exist.")
            return result.row

    async def update_permission(
        self,
        updater: Updater[PermissionRow],
    ) -> PermissionRow:
        """
        Update a permission.

        Args:
            updater: Updater with permission ID and fields to update

        Returns:
            Updated permission row

        Raises:
            ObjectNotFound: If permission does not exist
        """
        async with self._db.begin_session() as db_session:
            result = await execute_updater(db_session, updater)
            if result is None:
                raise ObjectNotFound(f"Permission with ID {updater.pk_value} does not exist.")
            return result.row

    async def _get_role(self, db_session: SASession, role_id: uuid.UUID) -> RoleRow:
        stmt = sa.select(RoleRow).where(RoleRow.id == role_id)
        role_row = await db_session.scalar(stmt)
        if role_row is None:
            raise RoleNotFound(f"Role with ID {role_id} does not exist.")
        return role_row

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
                raise ObjectNotFound(f"Role with ID {purger.spec.pk_value()} does not exist.")
            return result.row

    async def assign_role(self, data: UserRoleAssignmentInput) -> UserRoleRow:
        async with self._db.begin_session() as db_session:
            return await self._assign_role_in_session(db_session, data)

    async def _assign_role_in_session(
        self, db_session: SASession, data: UserRoleAssignmentInput
    ) -> UserRoleRow:
        creator = Creator(
            spec=UserRoleCreatorSpec(
                user_id=data.user_id,
                role_id=data.role_id,
                granted_by=None if data.granted_by is None else UserID(data.granted_by),
            )
        )
        result = await execute_creator(db_session, creator)
        return result.row

    async def revoke_role(self, data: UserRoleRevocationInput) -> RoleRevocationResult:
        """Revoke a role from a user.

        Returns (user_role_id, project_remaining_roles) where
        project_remaining_roles lists how many roles the user still
        holds in each project that this role belongs to.
        """
        async with self._db.begin_session() as db_session:
            user_role_row = await db_session.scalar(
                sa.select(UserRoleRow)
                .where(UserRoleRow.user_id == data.user_id)
                .where(UserRoleRow.role_id == data.role_id)
            )
            if user_role_row is None:
                raise RoleNotAssigned(
                    f"Role {data.role_id} is not assigned to user {data.user_id}."
                )
            user_role_id = user_role_row.id
            await db_session.delete(user_role_row)
            await db_session.flush()

            # Used by PermissionControllerService.revoke_role() to decide whether
            # to call ProjectDBSource.unbind_user_from_project().
            # TODO: remove this query when unbind_user_from_project() is retired
            # (i.e. association_groups_users is fully migrated to
            # association_scopes_entities).
            ase = AssociationScopesEntitiesRow
            project_subq = (
                sa.select(ase.scope_id).where(
                    ase.entity_type == LegacyEntityType.ROLE,
                    ase.scope_type == LegacyScopeType.PROJECT,
                    sa.cast(ase.entity_id, sa.String) == str(data.role_id),
                )
            ).subquery()

            rows = (
                await db_session.execute(
                    sa.select(ase.scope_id, sa.func.count(UserRoleRow.id))
                    .outerjoin(
                        UserRoleRow,
                        (sa.cast(UserRoleRow.role_id, sa.String) == ase.entity_id)
                        & (UserRoleRow.user_id == data.user_id),
                    )
                    .where(
                        ase.entity_type == LegacyEntityType.ROLE,
                        ase.scope_type == LegacyScopeType.PROJECT,
                        ase.scope_id.in_(sa.select(project_subq.c.scope_id)),
                    )
                    .group_by(ase.scope_id)
                )
            ).all()

            return RoleRevocationResult(
                user_role_id=user_role_id,
                project_remaining_roles=[
                    ProjectRoleCount(project_id=uuid.UUID(r[0]), remaining_count=r[1]) for r in rows
                ],
            )

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
            RoleNotFound: If role does not exist
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
                        permission=scoped_perm_input.permission,
                    )
                )
                await self._add_permission_to_group(db_session, perm_creator)

            # 2. Remove scoped permissions
            for perm_id in input_data.remove_scoped_permission_ids:
                perm_purger = Purger(spec=PermissionPurgerSpec(permission_id=perm_id))
                await self._remove_permission(db_session, perm_purger)

            # 3. Add object permissions
            for obj_perm_input in input_data.add_object_permissions:
                obj_perm_creator = Creator(
                    spec=ObjectPermissionCreatorSpec(
                        role_id=input_data.role_id,
                        entity_type=RBACElementType(obj_perm_input.entity_type.value),
                        entity_id=obj_perm_input.entity_id,
                        operation=obj_perm_input.operation,
                        status=obj_perm_input.status,
                    )
                )
                await self._add_object_permission_to_role(db_session, obj_perm_creator)

            # 4. Remove object permissions
            for obj_perm_id in input_data.remove_object_permission_ids:
                obj_perm_purger = Purger(
                    spec=ObjectPermissionPurgerSpec(object_permission_id=obj_perm_id)
                )
                await self._remove_object_permission_from_role(db_session, obj_perm_purger)

            # 5. Refresh and return
            await db_session.refresh(role_row)
            return role_row

    async def bulk_add_role_permissions(
        self,
        creator: BulkCreator[PermissionRow],
    ) -> BulkCreatorResultWithFailures[PermissionRow]:
        """Bulk-insert permission rows; per-row failures are reported separately."""
        async with self._db.begin_session_read_committed() as db_session:
            return await execute_bulk_creator_partial(db_session, creator)

    async def bulk_remove_role_permissions(
        self,
        purgers: list[Purger[PermissionRow]],
    ) -> BulkPurgerResultWithFailures[PermissionRow]:
        """Bulk-delete permission rows by primary key; per-row failures are reported separately."""
        async with self._db.begin_session_read_committed() as db_session:
            return await execute_bulk_purger_partial(db_session, purgers)

    async def replace_role_permissions(
        self,
        role_id: uuid.UUID,
        creator: BulkCreator[PermissionRow],
    ) -> BulkCreatorResultWithFailures[PermissionRow]:
        """
        Replace the role's entire scoped-permission set in a single transaction:
        delete all existing rows for ``role_id``, then bulk-insert the rows
        defined by ``creator.specs``. Passing a creator with no specs clears
        the role's permissions.

        - The role's existence is verified first; raises ``RoleNotFound``
          if the role does not exist.
        - Each permission row in ``creator.specs`` is assumed to carry the
          same ``role_id`` as the one passed to this method; the caller is
          responsible for keeping them aligned.
        """
        async with self._db.begin_session_read_committed() as db_session:
            await self._get_role(db_session, role_id)
            await db_session.execute(
                sa.delete(PermissionRow).where(PermissionRow.role_id == role_id)
            )
            return await execute_bulk_creator_partial(db_session, creator)

    async def get_role(self, role_id: uuid.UUID) -> RoleRow | None:
        async with self._db.begin_readonly_session_read_committed() as db_session:
            try:
                result = await self._get_role(db_session, role_id)
            except RoleNotFound:
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

    async def check_scope_permission_exist(
        self,
        user_id: uuid.UUID,
        scope_id: ScopeId,
        permission: Permission,
    ) -> bool:
        inner_query = (
            sa.select(sa.literal(1))
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
                        PermissionRow.scope_type == LegacyScopeType.GLOBAL,
                        PermissionRow.scope_id == scope_id.scope_id,
                    ),
                    PermissionRow.permission == permission,
                    PermissionRow.all_fields.is_(True),
                )
            )
        )
        role_query = sa.select(sa.exists(inner_query))
        async with self._db.begin_readonly_session_read_committed() as db_session:
            result = await db_session.scalar(role_query)
            return result or False

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
                    isouter=True,
                )
                .join(ObjectPermissionRow, RoleRow.id == ObjectPermissionRow.role_id)
            )
            .where(
                sa.and_(
                    RoleRow.status == RoleStatus.ACTIVE,
                    UserRoleRow.user_id == user_id,
                    sa.or_(
                        sa.and_(
                            PermissionRow.scope_type == LegacyScopeType.GLOBAL,
                            PermissionRow.permission == Permission.from_operation(operation),
                            PermissionRow.all_fields.is_(True),
                        ),
                        sa.and_(
                            AssociationScopesEntitiesRow.entity_id.in_(object_id_for_cond),
                            PermissionRow.permission == Permission.from_operation(operation),
                            PermissionRow.all_fields.is_(True),
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
            role_rows = list(role_rows_result.unique().all())

            for role in role_rows:
                for op in role.object_permission_rows:
                    object_id = op.object_id()
                    result[object_id] = True
        return result

    async def search_roles(
        self,
        querier: BatchQuerier,
    ) -> RoleListResult:
        """Searches roles with pagination and filtering."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(RoleRow)

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

    async def search_roles_in_scope(
        self,
        querier: BatchQuerier,
        scope: ScopedRoleOperationScope,
    ) -> RoleListResult:
        """Search roles registered in a given scope via association_scopes_entities."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(RoleRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
                scopes=[scope],
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
        scope: PermissionOperationScope | None = None,
    ) -> PermissionListResult:
        """Searches permissions with pagination and filtering."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(PermissionRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
                scopes=[scope] if scope is not None else (),
            )

            items = [row.PermissionRow.to_data() for row in result.rows]

            return PermissionListResult(
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
            query = sa.select(DomainRow.id, DomainRow.name)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [
                ScopeData(
                    id=ScopeId(scope_type=LegacyScopeType.DOMAIN, scope_id=str(row.id)),
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
            query = sa.select(ProjectRow.id, ProjectRow.name)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [
                ScopeData(
                    id=ScopeId(scope_type=LegacyScopeType.PROJECT, scope_id=str(row.id)),
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
                    id=ScopeId(scope_type=LegacyScopeType.USER, scope_id=str(row.uuid)),
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

    async def search_element_associations_in_scope(
        self,
        querier: BatchQuerier,
    ) -> ElementAssociationListResult:
        """Search element associations (full association rows) within a scope."""
        async with self._db.begin_readonly_session() as db_sess:
            query = sa.select(AssociationScopesEntitiesRow)

            result = await execute_batch_querier(
                db_sess,
                query,
                querier,
            )

            items = [row.AssociationScopesEntitiesRow.to_data() for row in result.rows]

            return ElementAssociationListResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    def _build_direct_scopes_cte(
        self,
        entity_type: LegacyEntityType,
        entity_ids: Sequence[str],
    ) -> sa.CTE:
        """Build the ``direct_scopes`` CTE for one ``(entity_type, entity_ids)`` group.

        Each input id → its direct AUTO parent scope(s). Result columns:
        ``(entity_id, scope_type, scope_id)``. Seeds :meth:`_build_scope_walk_cte`.
        """
        ase = AssociationScopesEntitiesRow.__table__
        return (
            sa.select(
                ase.c.entity_id,
                ase.c.scope_type,
                ase.c.scope_id,
            )
            .where(
                sa.and_(
                    ase.c.entity_type == entity_type,
                    ase.c.entity_id.in_(entity_ids),
                    ase.c.relation_type == RelationType.AUTO,
                )
            )
            .cte("direct_scopes")
        )

    def _build_scope_walk_cte(self, direct_scopes_cte: sa.CTE) -> sa.CTE:
        """Walk parent scopes upward from the unique scopes in ``direct_scopes_cte``.

        Carries only ``(start_scope_type, start_scope_id)`` through the
        recursion — entity_id is not carried. Keying the recursion on
        unique direct scopes keeps the working set at
        ``O(unique_direct_scopes * D)`` rather than ``O(K * D)`` when many
        input entities share the same direct parent scope.
        """
        ase = AssociationScopesEntitiesRow.__table__

        # Base case: unique direct scopes; start_scope == current scope.
        walk_base = sa.select(
            direct_scopes_cte.c.scope_type.label("start_scope_type"),
            direct_scopes_cte.c.scope_id.label("start_scope_id"),
            direct_scopes_cte.c.scope_type.label("scope_type"),
            direct_scopes_cte.c.scope_id.label("scope_id"),
        ).distinct()
        walk_cte = walk_base.cte("scope_walk", recursive=True)

        parent = ase.alias("parent")
        walk_recursive = (
            sa.select(
                walk_cte.c.start_scope_type,
                walk_cte.c.start_scope_id,
                parent.c.scope_type,
                parent.c.scope_id,
            )
            .select_from(
                parent.join(
                    walk_cte,
                    sa.and_(
                        parent.c.entity_type == walk_cte.c.scope_type,
                        parent.c.entity_id == walk_cte.c.scope_id,
                    ),
                )
            )
            .where(
                parent.c.relation_type == RelationType.AUTO,
            )
        )
        return walk_cte.union(walk_recursive)

    async def check_permission_with_scope_chain(
        self,
        data: ScopeChainPermissionCheckInput,
    ) -> bool:
        """Return whether the user holds every bit of ``permission`` on the target."""
        granted = await self._resolve_permissions_via_direct_scope_walk(
            [data.key], permission_filter=data.permission
        )
        return granted.get(data.key, Permission.NONE).covers(data.permission)

    async def check_bulk_permission_with_scope_chain(
        self,
        data: BulkPermissionCheckInput,
    ) -> Mapping[PermissionResolutionKey, bool]:
        """Check whether the user holds *operation* on each target key in one go.

        Returns a mapping from each input key to whether every bit of
        ``permission`` is granted.
        """
        if not data.keys:
            return {}
        granted = await self._resolve_permissions_via_direct_scope_walk(
            data.keys, permission_filter=data.permission
        )
        return {key: granted.get(key, Permission.NONE).covers(data.permission) for key in data.keys}

    async def _resolve_permissions_via_direct_scope_walk(
        self,
        keys: Collection[PermissionResolutionKey],
        *,
        permission_filter: Permission | None = None,
    ) -> Mapping[PermissionResolutionKey, Permission]:
        """Resolve granted operations for a collection of per-target keys.

        Groups input keys by ``(user_id, element_type, subject_entity_type)``
        and dispatches one SQL round-trip per group. Each group's query unions
        a scope-chain branch (walks parent AUTO scopes upward from each entity)
        and a self-scope branch (permission whose scope IS the entity itself).
        Returns a mapping keyed by the original ``PermissionResolutionKey``
        objects. Keys that received no grant map to ``Permission.NONE``.

        When ``permission_filter`` is set, only the bits of that mask are
        considered; otherwise every granted bit is returned.
        """
        if not keys:
            return {}

        groups: defaultdict[_PermissionGroupKey, list[PermissionResolutionKey]] = defaultdict(list)
        for key in keys:
            groups[
                _PermissionGroupKey(
                    user_id=key.user_id,
                    element_type=key.element_type,
                    subject_entity_type=key.subject_entity_type,
                )
            ].append(key)

        result: dict[PermissionResolutionKey, Permission] = {}
        async with self._db.begin_readonly_session_read_committed() as db_session:
            for group_key, members in groups.items():
                entity_ids = [k.entity_id for k in members]
                granted = await self._resolve_permissions_for_group(
                    db_session=db_session,
                    group_key=group_key,
                    entity_ids=entity_ids,
                    permission_filter=permission_filter,
                )
                for key in members:
                    result[key] = granted.get(key.entity_id, Permission.NONE)
        return result

    async def _resolve_permissions_for_group(
        self,
        *,
        db_session: SASession,
        group_key: _PermissionGroupKey,
        entity_ids: Sequence[str],
        permission_filter: Permission | None,
    ) -> Mapping[str, Permission]:
        """Run the scope-chain + self-scope query for a single
        ``(user_id, element_type, subject_entity_type)`` group with N entity_ids.

        Returns a mapping from entity_id to the granted bits. Entities that
        received no grant are absent from the returned mapping.
        """
        direct_scopes_cte = self._build_direct_scopes_cte(
            group_key.element_type.to_entity_type(), entity_ids
        )
        scope_walk_cte = self._build_scope_walk_cte(direct_scopes_cte)

        scope_chain_query = self._build_scope_chain_query(
            direct_scopes_cte, scope_walk_cte, group_key, permission_filter
        )
        self_scope_query = self._build_self_scope_query(group_key, entity_ids, permission_filter)
        combined_query = sa.union_all(scope_chain_query, self_scope_query)

        granted: defaultdict[str, Permission] = defaultdict(lambda: Permission.NONE)
        result = await db_session.execute(combined_query)
        for row in result:
            granted[row.entity_id] |= Permission(row.permission)
        return granted

    def _build_scope_chain_query(
        self,
        direct_scopes_cte: sa.CTE,
        scope_walk_cte: sa.CTE,
        group_key: _PermissionGroupKey,
        permission_filter: Permission | None,
    ) -> sa.Select[Any]:
        """Build the scope-chain branch: walk parent AUTO scopes upward from
        each entity's direct scope and pick up permissions along the way.
        """
        perm = PermissionRow.__table__
        user_roles = UserRoleRow.__table__
        roles = RoleRow.__table__

        filters: list[sa.ColumnElement[bool]] = [
            user_roles.c.user_id == group_key.user_id,
            roles.c.status == RoleStatus.ACTIVE,
            perm.c.entity_type == group_key.subject_entity_type.to_entity_type(),
            perm.c.all_fields.is_(True),
        ]
        if permission_filter is not None:
            filters.append(perm.c.permission.op("&")(permission_filter) != 0)

        return (
            sa.select(
                direct_scopes_cte.c.entity_id,
                perm.c.permission,
            )
            .select_from(
                direct_scopes_cte.join(
                    scope_walk_cte,
                    sa.and_(
                        scope_walk_cte.c.start_scope_type == direct_scopes_cte.c.scope_type,
                        scope_walk_cte.c.start_scope_id == direct_scopes_cte.c.scope_id,
                    ),
                )
                .join(
                    perm,
                    sa.and_(
                        perm.c.scope_type == scope_walk_cte.c.scope_type,
                        perm.c.scope_id == scope_walk_cte.c.scope_id,
                    ),
                )
                .join(roles, roles.c.id == perm.c.role_id)
                .join(user_roles, user_roles.c.role_id == roles.c.id)
            )
            .where(sa.and_(*filters))
        )

    def _build_self_scope_query(
        self,
        group_key: _PermissionGroupKey,
        entity_ids: Sequence[str],
        permission_filter: Permission | None,
    ) -> sa.Select[Any]:
        """Build the self-scope branch: pick up permissions whose scope IS
        the target entity itself.
        """
        perm = PermissionRow.__table__
        user_roles = UserRoleRow.__table__
        roles = RoleRow.__table__

        filters: list[sa.ColumnElement[bool]] = [
            user_roles.c.user_id == group_key.user_id,
            roles.c.status == RoleStatus.ACTIVE,
            perm.c.scope_type == group_key.element_type.to_scope_type(),
            perm.c.scope_id.in_(entity_ids),
            perm.c.entity_type == group_key.subject_entity_type.to_entity_type(),
            perm.c.all_fields.is_(True),
        ]
        if permission_filter is not None:
            filters.append(perm.c.permission.op("&")(permission_filter) != 0)

        return (
            sa.select(
                perm.c.scope_id.label("entity_id"),
                perm.c.permission,
            )
            .select_from(
                perm.join(roles, roles.c.id == perm.c.role_id).join(
                    user_roles, user_roles.c.role_id == roles.c.id
                )
            )
            .where(sa.and_(*filters))
        )

    async def resolve_effective_permissions(
        self,
        keys: Collection[PermissionResolutionKey],
    ) -> Mapping[PermissionResolutionKey, Permission]:
        """Resolve the effective permissions for a collection of per-target keys.

        Each input key represents one ``(user_id, element_type, entity_id,
        subject_entity_type)`` combination. The result is a mapping keyed by
        the same key object, with values being the bits the user holds on that
        entity.

        Keys sharing the same ``(user_id, element_type, subject_entity_type)``
        share one SQL round-trip; distinct groups dispatch separately. Keys
        that received no grant map to ``Permission.NONE``.
        """
        return await self._resolve_permissions_via_direct_scope_walk(keys)

    # ------------------------------------------------ virtual-entity-chain checks

    async def check_owned(
        self,
        key: OwnCheckKey,
        permission: Permission,
    ) -> bool:
        """Return whether the user holds *permission* on the key's entity via a virtual entity.

        Takes the bits the user holds on the entity through own and govern and tests
        that it covers *every* bit of ``permission``, which may be a mask
        (``UPSERT`` requires ``CREATE | UPDATE``) rather than a single bit.
        """
        resolved = await self.owned_permissions([key])
        return resolved.get(key, Permission.NONE).covers(permission)

    async def check_owned_all(
        self,
        keys: Collection[OwnCheckKey],
        permission: Permission,
    ) -> Mapping[OwnCheckKey, bool]:
        """The own check on each entity in one go.

        Returns a mapping from each input key to whether every bit of ``permission``
        is granted.
        """
        if not keys:
            return {}
        resolved = await self.owned_permissions(keys)
        return {key: resolved.get(key, Permission.NONE).covers(permission) for key in keys}

    async def check_governed(
        self,
        keys: Collection[GovernCheckKey],
        permission: Permission,
    ) -> Mapping[GovernCheckKey, bool]:
        """The govern check on each scope in one go.

        Returns a mapping from each input key to whether every bit of ``permission``
        is granted.
        """
        if not keys:
            return {}
        resolved = await self.governed_permissions(keys)
        return {key: resolved.get(key, Permission.NONE).covers(permission) for key in keys}

    async def owned_permissions(
        self,
        keys: Collection[OwnCheckKey],
    ) -> Mapping[OwnCheckKey, Permission]:
        """Resolve each target entity's effective :class:`Permission` through the
        graph; the walk is :meth:`PermissionReadOps.resolve_effective_permissions`."""
        if not keys:
            return {}
        async with self._ops.read_ops() as r:
            return await r.owned_permissions(keys)

    async def governed_permissions(
        self,
        keys: Collection[GovernCheckKey],
    ) -> Mapping[GovernCheckKey, Permission]:
        if not keys:
            return {}
        async with self._ops.read_ops() as r:
            return await r.governed_permissions(keys)

    async def bulk_assign_role(
        self, bulk_creator: BulkCreator[UserRoleRow]
    ) -> BulkCreatorResultWithFailures[UserRoleRow]:
        async with self._db.begin_session() as db_session:
            return await execute_bulk_creator_partial(db_session, bulk_creator)

    async def bulk_revoke_role(
        self, data: BulkUserRoleRevocationInput
    ) -> BulkRoleRevocationResultData:
        successes: list[UserRoleRevocationData] = []
        failures: list[BulkRoleRevocationFailure] = []

        async with self._db.begin_session() as db_session:
            for user_id in data.user_ids:
                try:
                    async with db_session.begin_nested():
                        stmt = (
                            sa.select(UserRoleRow)
                            .where(UserRoleRow.user_id == user_id)
                            .where(UserRoleRow.role_id == data.role_id)
                        )
                        user_role_row = await db_session.scalar(stmt)
                        if user_role_row is None:
                            raise RoleNotAssigned(
                                f"Role {data.role_id} is not assigned to user {user_id}."
                            )
                        user_role_id = user_role_row.id
                        await db_session.delete(user_role_row)
                        await db_session.flush()
                        successes.append(
                            UserRoleRevocationData(
                                user_role_id=user_role_id,
                                user_id=user_id,
                                role_id=data.role_id,
                            )
                        )
                except Exception as e:
                    log.warning(
                        "Failed to revoke role {} from user {}: {}",
                        data.role_id,
                        user_id,
                        str(e),
                    )
                    failures.append(BulkRoleRevocationFailure(user_id=user_id, message=str(e)))

        return BulkRoleRevocationResultData(successes=successes, failures=failures)
