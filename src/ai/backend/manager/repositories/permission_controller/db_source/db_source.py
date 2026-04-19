import logging
import uuid
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import contains_eager, selectinload

from ai.backend.common.data.permission.types import (
    RBACElementType,
    RelationType,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action.rbac_role_invitation import (
    AcceptRoleInvitationAction,
    CancelRoleInvitationAction,
    CreateRoleInvitationByEmailAction,
    CreateRoleInvitationResult,
    RejectRoleInvitationAction,
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
    RBACElementRef,
    ScopeData,
    ScopeListResult,
    ScopeType,
)
from ai.backend.manager.data.role_invitation.types import (
    RoleInvitationData,
    RoleInvitationState,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.common import GenericBadRequest, ObjectNotFound
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
from ai.backend.manager.models.role_invitation.conditions import RoleInvitationConditions
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import (
    BulkCreator,
    BulkCreatorResultWithFailures,
    Creator,
    execute_bulk_creator_partial,
    execute_creator,
)
from ai.backend.manager.repositories.base.purger import Purger, execute_purger
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACEntityCreator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.types import SearchScope
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
    RoleInvitationSearchResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class CreateRoleInput:
    """Input for creating a role with object permissions."""

    creator: Creator[RoleRow]
    object_permissions: Sequence[ObjectPermissionCreateInputBeforeRoleCreation]
    scope_refs: Sequence[RBACElementRef] = field(default_factory=list)


@dataclass(frozen=True)
class _ScopeChainQueryParams:
    user_id: uuid.UUID
    target_element_type: RBACElementType
    entity_ids: list[str]
    operation: OperationType
    permission_entity_type: EntityType | None = None


class PermissionDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @staticmethod
    async def _sync_user_scopes_on_assign(
        db_session: SASession,
        user_ids: Collection[uuid.UUID],
    ) -> None:
        """Ensure user-scope membership entries exist for all assigned roles.

        For each user, finds every scope bound to any of their assigned roles
        and inserts the corresponding user-scope entries.  Executed as a single
        ``INSERT … SELECT`` so the role lookup and insert share the same snapshot.
        """
        if not user_ids:
            return
        ase = AssociationScopesEntitiesRow
        source = (
            sa.select(
                ase.scope_type,
                ase.scope_id,
                sa.literal(EntityType.USER.value).label("entity_type"),
                sa.cast(UserRoleRow.user_id, sa.String).label("entity_id"),
                sa.literal(RelationType.AUTO.value).label("relation_type"),
            )
            .join(
                UserRoleRow,
                sa.cast(UserRoleRow.role_id, sa.String) == ase.entity_id,
            )
            .where(
                ase.entity_type == EntityType.ROLE,
                UserRoleRow.user_id.in_(user_ids),
            )
        )
        await db_session.execute(
            pg_insert(ase)
            .from_select(
                ["scope_type", "scope_id", "entity_type", "entity_id", "relation_type"],
                source,
            )
            .on_conflict_do_nothing()
        )

    @staticmethod
    async def _sync_user_scopes_on_revoke(
        db_session: SASession,
        user_ids: Collection[uuid.UUID],
    ) -> None:
        """Remove user-scope entries no longer covered by any assigned role.

        Deletes user-scope rows for *user_ids* when no assigned role binds
        the user to that scope.  Executed as a single ``DELETE`` statement
        so the coverage check and deletion share the same snapshot.
        """
        if not user_ids:
            return
        ase = AssociationScopesEntitiesRow
        str_user_ids = [str(uid) for uid in user_ids]
        ase_remaining = sa.orm.aliased(ase, flat=True)
        await db_session.execute(
            sa.delete(ase).where(
                ase.entity_type == EntityType.USER,
                ase.entity_id.in_(str_user_ids),
                ~sa.exists(
                    sa.select(sa.literal(1))
                    .select_from(ase_remaining)
                    .join(
                        UserRoleRow,
                        sa.cast(UserRoleRow.role_id, sa.String) == ase_remaining.entity_id,
                    )
                    .where(
                        ase_remaining.entity_type == EntityType.ROLE,
                        ase_remaining.scope_type == ase.scope_type,
                        ase_remaining.scope_id == ase.scope_id,
                        sa.cast(UserRoleRow.user_id, sa.String) == ase.entity_id,
                    )
                ),
            )
        )

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
            return await self._assign_role_in_session(db_session, data)

    @staticmethod
    async def _assign_role_in_session(
        db_session: SASession, data: UserRoleAssignmentInput
    ) -> UserRoleRow:
        creator = Creator(
            spec=UserRoleCreatorSpec(
                user_id=data.user_id,
                role_id=data.role_id,
                granted_by=data.granted_by,
            )
        )
        result = await execute_creator(db_session, creator)
        await PermissionDBSource._sync_user_scopes_on_assign(db_session, [data.user_id])
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

            await self._sync_user_scopes_on_revoke(db_session, [data.user_id])

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
                scope=scope,
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

    @staticmethod
    def _build_scope_chain_cte(
        target_entity_type: EntityType,
        entity_ids: list[str],
    ) -> sa.CTE:
        """Build a recursive CTE that walks the scope chain upward via AUTO edges.

        Carries entity_id through the recursion so each result row can be
        traced back to its originating entity.
        """
        ase = AssociationScopesEntitiesRow.__table__

        # Base case: direct AUTO scope entries for target entities.
        scope_chain_base = sa.select(
            ase.c.entity_id,
            ase.c.scope_type,
            ase.c.scope_id,
        ).where(
            sa.and_(
                ase.c.entity_type == target_entity_type,
                ase.c.entity_id.in_(entity_ids),
                ase.c.relation_type == RelationType.AUTO,
            )
        )
        scope_chain_cte = scope_chain_base.cte("scope_chain", recursive=True)

        # Recursive case: walk parent scopes upward, carrying entity_id.
        parent = ase.alias("parent")
        scope_chain_recursive = (
            sa.select(
                scope_chain_cte.c.entity_id,
                parent.c.scope_type,
                parent.c.scope_id,
            )
            .select_from(
                parent.join(
                    scope_chain_cte,
                    sa.and_(
                        parent.c.entity_type == scope_chain_cte.c.scope_type,
                        parent.c.entity_id == scope_chain_cte.c.scope_id,
                    ),
                )
            )
            .where(
                parent.c.relation_type == RelationType.AUTO,
            )
        )
        return scope_chain_cte.union(scope_chain_recursive)

    async def _check_permissions_via_scope_chain(
        self,
        params: _ScopeChainQueryParams,
    ) -> set[str]:
        """Core scope chain permission check shared by single and batch methods.

        Two-layer check:
        1. Scope chain traversal — walks AUTO edges upward via recursive CTE.
        2. Self-scope direct match — permission scoped to the target entity itself.

        Returns the set of entity IDs that have the requested permission.
        """
        association_entity_type = params.target_element_type.to_entity_type()
        permission_entity_type = params.permission_entity_type or association_entity_type
        target_scope_type = params.target_element_type.to_scope_type()

        permissions = PermissionRow.__table__
        user_roles = UserRoleRow.__table__
        roles = RoleRow.__table__

        # Layer 1: scope chain traversal.
        scope_chain_cte = self._build_scope_chain_cte(association_entity_type, params.entity_ids)
        scope_chain_query = (
            sa.select(scope_chain_cte.c.entity_id)
            .select_from(
                scope_chain_cte.join(
                    permissions,
                    sa.and_(
                        permissions.c.scope_type == scope_chain_cte.c.scope_type,
                        permissions.c.scope_id == scope_chain_cte.c.scope_id,
                    ),
                )
                .join(
                    roles,
                    roles.c.id == permissions.c.role_id,
                )
                .join(
                    user_roles,
                    user_roles.c.role_id == roles.c.id,
                )
            )
            .where(
                sa.and_(
                    user_roles.c.user_id == params.user_id,
                    roles.c.status == RoleStatus.ACTIVE,
                    permissions.c.entity_type == permission_entity_type,
                    permissions.c.operation == params.operation,
                )
            )
        )

        # Layer 2: self-scope direct match.
        self_scope_query = (
            sa.select(permissions.c.scope_id.label("entity_id"))
            .select_from(
                permissions.join(
                    roles,
                    roles.c.id == permissions.c.role_id,
                ).join(
                    user_roles,
                    user_roles.c.role_id == roles.c.id,
                )
            )
            .where(
                sa.and_(
                    user_roles.c.user_id == params.user_id,
                    roles.c.status == RoleStatus.ACTIVE,
                    permissions.c.scope_type == target_scope_type,
                    permissions.c.scope_id.in_(params.entity_ids),
                    permissions.c.entity_type == permission_entity_type,
                    permissions.c.operation == params.operation,
                )
            )
        )

        combined_query = sa.union(scope_chain_query, self_scope_query)

        granted: set[str] = set()
        async with self._db.begin_readonly_session_read_committed() as db_session:
            rows = await db_session.execute(combined_query)
            for row in rows:
                granted.add(row.entity_id)

        return granted

    async def check_permission_with_scope_chain(
        self,
        data: ScopeChainPermissionCheckInput,
    ) -> bool:
        """CTE-based permission check for a single entity."""
        granted = await self._check_permissions_via_scope_chain(
            _ScopeChainQueryParams(
                user_id=data.user_id,
                target_element_type=data.target_element_ref.element_type,
                entity_ids=[data.target_element_ref.element_id],
                operation=data.operation,
                permission_entity_type=data.permission_entity_type,
            )
        )
        return data.target_element_ref.element_id in granted

    async def check_bulk_permission_with_scope_chain(
        self,
        data: BulkPermissionCheckInput,
    ) -> dict[str, bool]:
        """Batch CTE-based permission check for multiple entities."""
        if not data.target_entity_ids:
            return {}

        granted = await self._check_permissions_via_scope_chain(
            _ScopeChainQueryParams(
                user_id=data.user_id,
                target_element_type=data.target_element_type,
                entity_ids=data.target_entity_ids,
                operation=data.operation,
            )
        )
        return {eid: eid in granted for eid in data.target_entity_ids}

    async def bulk_assign_role(
        self, bulk_creator: BulkCreator[UserRoleRow]
    ) -> BulkCreatorResultWithFailures[UserRoleRow]:
        async with self._db.begin_session() as db_session:
            result = await execute_bulk_creator_partial(db_session, bulk_creator)
            all_user_ids = [row.user_id for row in result.successes]
            await self._sync_user_scopes_on_assign(db_session, all_user_ids)
            return result

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
            revoked_user_ids = [s.user_id for s in successes]
            await self._sync_user_scopes_on_revoke(db_session, revoked_user_ids)

        return BulkRoleRevocationResultData(successes=successes, failures=failures)

    # -- role invitation --

    async def create_invitation_by_email(
        self,
        action: CreateRoleInvitationByEmailAction,
    ) -> CreateRoleInvitationResult:
        """Resolve emails and create invitations in a single transaction.

        Emails that don't resolve to an ACTIVE user are silently skipped.
        Duplicate active invitations (caught by the partial unique index)
        are also silently skipped.
        """
        async with self._db.begin_session_read_committed() as session:
            email_to_user_id = await self._resolve_invitation_emails(session, action.invitee_emails)
            specs = [
                RoleInvitationCreatorSpec(
                    inviter_user_id=action.inviter_user_id,
                    invitee_user_id=user_id,
                    role_id=action.role_id,
                )
                for email in action.invitee_emails
                if (user_id := email_to_user_id.get(email)) is not None
            ]
            if not specs:
                return CreateRoleInvitationResult()
            result = await execute_bulk_creator_partial(session, BulkCreator(specs=specs))
            return CreateRoleInvitationResult(
                created=[row.to_data() for row in result.successes],
            )

    async def search_invitations(
        self,
        querier: BatchQuerier,
        scope: SearchScope | None = None,
    ) -> RoleInvitationSearchResult:
        async with self._db.begin_readonly_session_read_committed() as session:
            query = sa.select(RoleInvitationRow)
            result = await execute_batch_querier(session, query, querier, scope=scope)
            items = [row.RoleInvitationRow.to_data() for row in result.rows]
            return RoleInvitationSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def accept_invitation(
        self,
        action: AcceptRoleInvitationAction,
    ) -> RoleInvitationData:
        """Transition PENDING→ACCEPTED and assign the role in one session."""
        async with self._db.begin_session_read_committed() as session:
            row = await self._get_invitation_to_accept(session, action.invitation_id)
            row.state = RoleInvitationState.ACCEPTED
            await self._assign_role_in_session(
                session,
                UserRoleAssignmentInput(user_id=row.invitee_user_id, role_id=row.role_id),
            )
            await session.flush()
            await session.refresh(row)
            return row.to_data()

    async def reject_invitation(
        self,
        action: RejectRoleInvitationAction,
    ) -> RoleInvitationData:
        async with self._db.begin_session_read_committed() as session:
            row = await self._get_invitation_to_reject(session, action.invitation_id)
            row.state = RoleInvitationState.REJECTED
            await session.flush()
            await session.refresh(row)
            return row.to_data()

    async def cancel_invitation(
        self,
        action: CancelRoleInvitationAction,
    ) -> RoleInvitationData:
        async with self._db.begin_session_read_committed() as session:
            row = await self._get_invitation_to_cancel(session, action.invitation_id)
            row.state = RoleInvitationState.CANCELED
            await session.flush()
            await session.refresh(row)
            return row.to_data()

    @staticmethod
    async def _get_invitation_to_accept(
        session: SASession, invitation_id: uuid.UUID
    ) -> RoleInvitationRow:
        """Fetch a PENDING invitation for acceptance.

        Raises ObjectNotFound if not found.
        Raises GenericBadRequest if already accepted, rejected, or canceled.
        """
        cond_id = RoleInvitationConditions.by_id(invitation_id)
        stmt = sa.select(RoleInvitationRow).where(cond_id())
        row = await session.scalar(stmt)
        if row is None:
            raise ObjectNotFound(object_name="RoleInvitation")
        if row.state != RoleInvitationState.PENDING:
            raise GenericBadRequest(
                f"Cannot accept: invitation is {row.state.value}, expected pending"
            )
        return row

    @staticmethod
    async def _get_invitation_to_reject(
        session: SASession, invitation_id: uuid.UUID
    ) -> RoleInvitationRow:
        """Fetch a PENDING invitation for rejection.

        Already rejected invitations are silently returned (idempotent).
        Raises ObjectNotFound if not found.
        Raises GenericBadRequest if accepted or canceled.
        """
        cond_id = RoleInvitationConditions.by_id(invitation_id)
        stmt = sa.select(RoleInvitationRow).where(cond_id())
        row = await session.scalar(stmt)
        if row is None:
            raise ObjectNotFound(object_name="RoleInvitation")
        if row.state == RoleInvitationState.REJECTED:
            return row
        if row.state != RoleInvitationState.PENDING:
            raise GenericBadRequest(
                f"Cannot reject: invitation is {row.state.value}, expected pending"
            )
        return row

    @staticmethod
    async def _get_invitation_to_cancel(
        session: SASession, invitation_id: uuid.UUID
    ) -> RoleInvitationRow:
        """Fetch a PENDING invitation for cancellation.

        Already canceled invitations are silently returned (idempotent).
        Raises ObjectNotFound if not found.
        Raises GenericBadRequest if accepted or rejected.
        """
        cond_id = RoleInvitationConditions.by_id(invitation_id)
        stmt = sa.select(RoleInvitationRow).where(cond_id())
        row = await session.scalar(stmt)
        if row is None:
            raise ObjectNotFound(object_name="RoleInvitation")
        if row.state == RoleInvitationState.CANCELED:
            return row
        if row.state != RoleInvitationState.PENDING:
            raise GenericBadRequest(
                f"Cannot cancel: invitation is {row.state.value}, expected pending"
            )
        return row

    @staticmethod
    async def _resolve_invitation_emails(
        session: SASession,
        emails: list[str],
    ) -> dict[str, uuid.UUID]:
        """Resolve emails to user UUIDs (ACTIVE users only)."""
        stmt = sa.select(UserRow.email, UserRow.uuid).where(
            UserRow.status == UserStatus.ACTIVE,
            UserRow.email.in_(emails),
        )
        result = await session.execute(stmt)
        return {row.email: row.uuid for row in result.all()}
