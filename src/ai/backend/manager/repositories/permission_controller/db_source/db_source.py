import logging
import uuid
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import contains_eager, selectinload

from ai.backend.common.data.permission.types import (
    RBACElementType,
    RelationType,
)
from ai.backend.common.identifier.entity import EntityID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action.rbac_role_invitation import (
    CreateRoleInvitationResult,
)
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
    EntityType,
    OperationType,
    Permission,
    RBACElementRef,
    ScopeData,
    ScopeListResult,
    ScopeType,
)
from ai.backend.manager.data.permission.virtual_scope import VirtualScopePermissionCheckKey
from ai.backend.manager.data.role_invitation.types import (
    RoleInvitationData,
    RoleInvitationState,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.permission import RoleNotAssigned, RoleNotFound
from ai.backend.manager.errors.role_invitation import (
    DuplicateRoleInvitationError,
    RoleInvitationInvalidState,
    RoleInvitationNotFound,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
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
from ai.backend.manager.repositories.permission_controller.creators import (
    ObjectPermissionCreatorSpec,
    PermissionCreatorSpec,
    UserRoleCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.types import (
    PermissionSearchScope,
    ScopedRoleSearchScope,
)
from ai.backend.manager.repositories.role_invitation.creators import (
    RoleInvitationCreatorSpec,
)
from ai.backend.manager.repositories.role_invitation.types import (
    InviteeSearchScope,
    InviterSearchScope,
    RoleInvitationSearchResult,
    RoleInvitationSearchScope,
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


@dataclass(frozen=True)
class _VirtualScopePermissionGroupKey:
    """Group key for batching virtual-scope-chain resolution inputs.

    Keys sharing the same ``(user_id, entity_type)`` are resolved by a single
    SQL round-trip differing only in the per-target ``entity_id`` IN-list.
    ``entity_type`` is the DB-facing :class:`EntityType` enum (converted from the
    open ``EntityRef.entity_type``) so it binds against the permission columns.
    """

    user_id: uuid.UUID
    entity_type: EntityType


class PermissionDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

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
                raise ObjectNotFound(f"Permission with ID {purger.pk_value} does not exist.")
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
                raise ObjectNotFound(f"Role with ID {purger.pk_value} does not exist.")
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
                granted_by=data.granted_by,
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
            # to call GroupDBSource.unbind_user_from_project().
            # TODO: remove this query when unbind_user_from_project() is retired
            # (i.e. association_groups_users is fully migrated to
            # association_scopes_entities).
            ase = AssociationScopesEntitiesRow
            project_subq = (
                sa.select(ase.scope_id).where(
                    ase.entity_type == EntityType.ROLE,
                    ase.scope_type == ScopeType.PROJECT,
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
                        ase.entity_type == EntityType.ROLE,
                        ase.scope_type == ScopeType.PROJECT,
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
                        scope_type=RBACElementType(scoped_perm_input.scope_type.value),
                        scope_id=scoped_perm_input.scope_id,
                        entity_type=RBACElementType(scoped_perm_input.entity_type.value),
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
                        entity_type=RBACElementType(obj_perm_input.entity_type.value),
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
        operation: OperationType,
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
                        PermissionRow.scope_type == ScopeType.GLOBAL,
                        PermissionRow.scope_id == scope_id.scope_id,
                    ),
                    PermissionRow.operation == operation,
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
        scope: ScopedRoleSearchScope,
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
        scope: PermissionSearchScope | None = None,
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
        entity_type: EntityType,
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
        """Return whether the user holds *operation* on the target element."""
        granted = await self._resolve_permissions_via_direct_scope_walk(
            [data.key], operation_filter=data.operation
        )
        return data.operation in granted.get(data.key, frozenset())

    async def check_bulk_permission_with_scope_chain(
        self,
        data: BulkPermissionCheckInput,
    ) -> Mapping[PermissionResolutionKey, bool]:
        """Check whether the user holds *operation* on each target key in one go.

        Returns a mapping from each input key to a boolean indicating whether
        the operation is granted.
        """
        if not data.keys:
            return {}
        granted = await self._resolve_permissions_via_direct_scope_walk(
            data.keys, operation_filter=data.operation
        )
        return {key: data.operation in granted.get(key, frozenset()) for key in data.keys}

    async def _resolve_permissions_via_direct_scope_walk(
        self,
        keys: Collection[PermissionResolutionKey],
        *,
        operation_filter: OperationType | None = None,
    ) -> Mapping[PermissionResolutionKey, frozenset[OperationType]]:
        """Resolve granted operations for a collection of per-target keys.

        Groups input keys by ``(user_id, element_type, subject_entity_type)``
        and dispatches one SQL round-trip per group. Each group's query unions
        a scope-chain branch (walks parent AUTO scopes upward from each entity)
        and a self-scope branch (permission whose scope IS the entity itself).
        Returns a mapping keyed by the original ``PermissionResolutionKey``
        objects. Keys that received no grant map to an empty frozenset.

        When ``operation_filter`` is set, only that operation is considered;
        otherwise every granted operation is returned.
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

        result: dict[PermissionResolutionKey, frozenset[OperationType]] = {}
        async with self._db.begin_readonly_session_read_committed() as db_session:
            for group_key, members in groups.items():
                entity_ids = [k.entity_id for k in members]
                granted = await self._resolve_permissions_for_group(
                    db_session=db_session,
                    group_key=group_key,
                    entity_ids=entity_ids,
                    operation_filter=operation_filter,
                )
                for key in members:
                    result[key] = frozenset(granted.get(key.entity_id, ()))
        return result

    async def _resolve_permissions_for_group(
        self,
        *,
        db_session: SASession,
        group_key: _PermissionGroupKey,
        entity_ids: Sequence[str],
        operation_filter: OperationType | None,
    ) -> Mapping[str, set[OperationType]]:
        """Run the scope-chain + self-scope query for a single
        ``(user_id, element_type, subject_entity_type)`` group with N entity_ids.

        Returns a mapping from entity_id to the set of granted operations.
        Entities that received no grant are absent from the returned mapping.
        """
        direct_scopes_cte = self._build_direct_scopes_cte(
            group_key.element_type.to_entity_type(), entity_ids
        )
        scope_walk_cte = self._build_scope_walk_cte(direct_scopes_cte)

        scope_chain_query = self._build_scope_chain_query(
            direct_scopes_cte, scope_walk_cte, group_key, operation_filter
        )
        self_scope_query = self._build_self_scope_query(group_key, entity_ids, operation_filter)
        combined_query = sa.union_all(scope_chain_query, self_scope_query)

        granted: defaultdict[str, set[OperationType]] = defaultdict(set)
        result = await db_session.execute(combined_query)
        for row in result:
            granted[row.entity_id].add(row.operation)
        return granted

    def _build_scope_chain_query(
        self,
        direct_scopes_cte: sa.CTE,
        scope_walk_cte: sa.CTE,
        group_key: _PermissionGroupKey,
        operation_filter: OperationType | None,
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
        ]
        if operation_filter is not None:
            filters.append(perm.c.operation == operation_filter)

        return (
            sa.select(
                direct_scopes_cte.c.entity_id,
                perm.c.operation,
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
        operation_filter: OperationType | None,
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
        ]
        if operation_filter is not None:
            filters.append(perm.c.operation == operation_filter)

        return (
            sa.select(
                perm.c.scope_id.label("entity_id"),
                perm.c.operation,
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
    ) -> Mapping[PermissionResolutionKey, frozenset[OperationType]]:
        """Resolve the effective permissions for a collection of per-target keys.

        Each input key represents one ``(user_id, element_type, entity_id,
        subject_entity_type)`` combination. The result is a mapping keyed by
        the same key object, with values being the set of operations the user
        is authorized to perform on that entity.

        Keys sharing the same ``(user_id, element_type, subject_entity_type)``
        share one SQL round-trip; distinct groups dispatch separately. Keys
        that received no grant map to an empty frozenset.
        """
        return await self._resolve_permissions_via_direct_scope_walk(keys)

    # ------------------------------------------------ virtual-scope-chain checks

    async def check_permission_via_virtual_scope(
        self,
        key: VirtualScopePermissionCheckKey,
        permission: Permission,
    ) -> bool:
        """Return whether the user holds *permission* on the key's entity via a virtual scope.

        Resolves the effective permission through the virtual-scope chain and tests
        it bitwise (``effective & permission != NONE``).
        """
        resolved = await self.resolve_effective_permissions_via_virtual_scope([key])
        return bool(resolved.get(key, Permission.NONE) & permission)

    async def check_bulk_permission_via_virtual_scope(
        self,
        keys: Collection[VirtualScopePermissionCheckKey],
        permission: Permission,
    ) -> Mapping[VirtualScopePermissionCheckKey, bool]:
        """Check *permission* on each target key through the virtual-scope chain in one go.

        Returns a mapping from each input key to whether the permission is granted.
        """
        if not keys:
            return {}
        resolved = await self.resolve_effective_permissions_via_virtual_scope(keys)
        return {key: bool(resolved.get(key, Permission.NONE) & permission) for key in keys}

    async def resolve_effective_permissions_via_virtual_scope(
        self,
        keys: Collection[VirtualScopePermissionCheckKey],
    ) -> Mapping[VirtualScopePermissionCheckKey, Permission]:
        """Resolve each target's effective :class:`Permission` through the virtual-scope chain.

        Walks ``entity -> entity_memberships -> scope_bindings -> scope`` and
        OR-combines the granted bitmask at each resolved scope, clipping every
        path by both hop caps (``granted & scope_cap & entity_cap``; ``None`` = no
        ceiling). Keys sharing ``(user_id, entity_type)`` share one round-trip;
        keys with no reachable grant map to :attr:`Permission.NONE`.
        """
        if not keys:
            return {}

        groups: defaultdict[
            _VirtualScopePermissionGroupKey, list[VirtualScopePermissionCheckKey]
        ] = defaultdict(list)
        for key in keys:
            groups[
                _VirtualScopePermissionGroupKey(
                    user_id=key.user_id,
                    entity_type=EntityType(key.entity.entity_type),
                )
            ].append(key)

        result: dict[VirtualScopePermissionCheckKey, Permission] = {}
        async with self._db.begin_readonly_session_read_committed() as db_session:
            for group_key, members in groups.items():
                entity_ids = [k.entity.entity_id for k in members]
                granted = await self._resolve_permissions_for_virtual_scope_group(
                    db_session=db_session,
                    group_key=group_key,
                    entity_ids=entity_ids,
                )
                for key in members:
                    result[key] = granted.get(key.entity.entity_id, Permission.NONE)
        return result

    async def _resolve_permissions_for_virtual_scope_group(
        self,
        *,
        db_session: SASession,
        group_key: _VirtualScopePermissionGroupKey,
        entity_ids: Sequence[EntityID],
    ) -> Mapping[EntityID, Permission]:
        """Run the virtual-scope-chain query for a single ``(user_id, entity_type)``
        group with N entity_ids.

        Returns a mapping from entity_id to its effective (cap-clipped, OR-combined)
        :class:`Permission`. Entities with no reachable grant are absent from the map.
        """
        em = EntityMembershipRow.__table__
        sb = ScopeBindingRow.__table__
        perm = PermissionRow.__table__
        roles = RoleRow.__table__
        user_roles = UserRoleRow.__table__

        query = (
            sa.select(
                em.c.entity_id,
                perm.c.permission,
                sb.c.permission_cap.label("scope_cap"),
                em.c.permission_cap.label("entity_cap"),
            )
            .select_from(
                em.join(sb, sb.c.virtual_scope_id == em.c.virtual_scope_id)
                .join(
                    perm,
                    sa.and_(
                        perm.c.scope_type == sb.c.scope_type,
                        # scope_bindings.scope_id is a native UUID; permissions.scope_id
                        # stores its canonical string form. Cast to compare.
                        perm.c.scope_id == sa.cast(sb.c.scope_id, sa.String),
                        perm.c.entity_type == group_key.entity_type,
                    ),
                )
                .join(roles, roles.c.id == perm.c.role_id)
                .join(user_roles, user_roles.c.role_id == roles.c.id)
            )
            .where(
                em.c.entity_type == group_key.entity_type,
                em.c.entity_id.in_(entity_ids),
                user_roles.c.user_id == group_key.user_id,
                roles.c.status == RoleStatus.ACTIVE,
            )
        )

        full_cap = Permission.full()
        granted: defaultdict[EntityID, Permission] = defaultdict(lambda: Permission.NONE)
        result = await db_session.execute(query)
        for row in result:
            scope_cap = row.scope_cap if row.scope_cap is not None else full_cap
            entity_cap = row.entity_cap if row.entity_cap is not None else full_cap
            granted[row.entity_id] |= row.permission & scope_cap & entity_cap
        return granted

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

    # -- role invitation --

    async def create_invitation_by_email(
        self,
        *,
        invitee_emails: list[str],
        inviter_user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> CreateRoleInvitationResult:
        """Resolve emails and create invitations in a single transaction.

        Emails that don't resolve to exactly one ACTIVE user are silently skipped.
        Duplicate active invitations (caught by the partial unique index)
        are also silently skipped.
        """
        async with self._db.begin_session_read_committed() as session:
            email_to_user_id = await self._resolve_invitation_emails(session, invitee_emails)
            creators = [
                RBACEntityCreator(
                    spec=RoleInvitationCreatorSpec(
                        inviter_user_id=inviter_user_id,
                        invitee_user_id=invitee_user_id,
                        role_id=role_id,
                    ),
                    element_type=RBACElementType.ROLE_ASSIGNMENT,
                    scope_ref=RBACElementRef(
                        element_type=RBACElementType.USER,
                        element_id=str(invitee_user_id),
                    ),
                    additional_scope_refs=[
                        RBACElementRef(
                            element_type=RBACElementType.ROLE,
                            element_id=str(role_id),
                        ),
                    ],
                )
                for email in invitee_emails
                if (invitee_user_id := email_to_user_id.get(email)) is not None
            ]
            if not creators:
                return CreateRoleInvitationResult()

            created_rows: list[RoleInvitationRow] = []
            for creator in creators:
                async with session.begin_nested():
                    try:
                        row = (await execute_rbac_entity_creator(session, creator)).row
                    except DuplicateRoleInvitationError:
                        continue
                    created_rows.append(row)
            return CreateRoleInvitationResult(
                created=[row.to_data() for row in created_rows],
            )

    async def search_invitations_by_invitee(
        self,
        querier: BatchQuerier,
        scope: InviteeSearchScope,
    ) -> RoleInvitationSearchResult:
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(RoleInvitationRow)
            result = await execute_batch_querier(session, query, querier, scopes=[scope])
            items = [row.RoleInvitationRow.to_data() for row in result.rows]
            return RoleInvitationSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_invitations_by_inviter(
        self,
        querier: BatchQuerier,
        scope: InviterSearchScope,
    ) -> RoleInvitationSearchResult:
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(RoleInvitationRow)
            result = await execute_batch_querier(session, query, querier, scopes=[scope])
            items = [row.RoleInvitationRow.to_data() for row in result.rows]
            return RoleInvitationSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_invitations_by_role(
        self,
        querier: BatchQuerier,
        scope: RoleInvitationSearchScope,
    ) -> RoleInvitationSearchResult:
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(RoleInvitationRow)
            result = await execute_batch_querier(session, query, querier, scopes=[scope])
            items = [row.RoleInvitationRow.to_data() for row in result.rows]
            return RoleInvitationSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def admin_search_invitations(
        self,
        querier: BatchQuerier,
    ) -> RoleInvitationSearchResult:
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(RoleInvitationRow)
            result = await execute_batch_querier(session, query, querier)
            items = [row.RoleInvitationRow.to_data() for row in result.rows]
            return RoleInvitationSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def accept_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> RoleInvitationData:
        """Transition PENDING→ACCEPTED and assign the role in one session."""
        async with self._db.begin_session_read_committed() as session:
            row = await self._update_invitation_state(
                session, invitation_id, RoleInvitationState.ACCEPTED
            )
            if row is None:
                existing = await self._get_failed_invitation(session, invitation_id)
                raise RoleInvitationInvalidState(
                    f"Cannot accept: invitation is {existing.state.value}, expected pending"
                )
            await self._assign_role_in_session(
                session,
                UserRoleAssignmentInput(user_id=row.invitee_user_id, role_id=row.role_id),
            )
            return row.to_data()

    async def reject_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> RoleInvitationData:
        async with self._db.begin_session_read_committed() as session:
            row = await self._update_invitation_state(
                session, invitation_id, RoleInvitationState.REJECTED
            )
            if row is not None:
                return row.to_data()
            existing = await self._get_failed_invitation(session, invitation_id)
            if existing.state == RoleInvitationState.REJECTED:
                return existing.to_data()
            raise RoleInvitationInvalidState(
                f"Cannot reject: invitation is {existing.state.value}, expected pending"
            )

    async def cancel_invitation(
        self,
        invitation_id: uuid.UUID,
    ) -> RoleInvitationData:
        async with self._db.begin_session_read_committed() as session:
            row = await self._update_invitation_state(
                session, invitation_id, RoleInvitationState.CANCELED
            )
            if row is not None:
                return row.to_data()
            existing = await self._get_failed_invitation(session, invitation_id)
            if existing.state == RoleInvitationState.CANCELED:
                return existing.to_data()
            raise RoleInvitationInvalidState(
                f"Cannot cancel: invitation is {existing.state.value}, expected pending"
            )

    @staticmethod
    async def _update_invitation_state(
        session: SASession,
        invitation_id: uuid.UUID,
        target_state: RoleInvitationState,
    ) -> RoleInvitationRow | None:
        """UPDATE PENDING→*target_state* with RETURNING; None if no row matched."""
        update_stmt = (
            sa.update(RoleInvitationRow)
            .where(
                RoleInvitationRow.id == invitation_id,
                RoleInvitationRow.state == RoleInvitationState.PENDING,
            )
            .values(state=target_state)
            .returning(*RoleInvitationRow.__table__.columns)
        )
        result = await session.execute(sa.select(RoleInvitationRow).from_statement(update_stmt))
        return cast(RoleInvitationRow | None, result.scalar_one_or_none())

    @staticmethod
    async def _get_failed_invitation(
        session: SASession,
        invitation_id: uuid.UUID,
    ) -> RoleInvitationRow:
        """Fetch the row that caused an update to match no row.

        Raises RoleInvitationNotFound if the row does not exist. The caller
        inspects the returned row's state to decide idempotent vs. invalid.
        """
        existing = await session.scalar(
            sa.select(RoleInvitationRow).where(RoleInvitationRow.id == invitation_id)
        )
        if existing is None:
            raise RoleInvitationNotFound()
        return existing

    @staticmethod
    async def _resolve_invitation_emails(
        session: SASession,
        emails: Collection[str],
    ) -> dict[str, uuid.UUID]:
        """Resolve emails to user UUIDs (ACTIVE users only).

        Emails that don't match exactly one ACTIVE user are silently skipped.
        """
        if not emails:
            return {}
        stmt = sa.select(UserRow.email, UserRow.uuid).where(
            UserRow.status == UserStatus.ACTIVE,
            UserRow.email.in_(emails),
        )
        result = await session.execute(stmt)
        rows = result.all()

        resolved: dict[str, uuid.UUID] = {}
        for row in rows:
            resolved[row.email] = row.uuid
        return resolved
