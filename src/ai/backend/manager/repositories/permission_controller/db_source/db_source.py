import logging
import uuid
from collections.abc import Collection, Mapping, Sequence

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import selectinload

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.permission import (
    PermissionData,
    PermissionListResult,
)
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    AssignedUserListResult,
    BulkRoleRevocationFailure,
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
    ProjectRoleCount,
    RoleListResult,
    RoleRevocationResult,
    UserRoleAssignmentInput,
    UserRoleRevocationData,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.types import (
    Permission,
    ScopeData,
    ScopeListResult,
)
from ai.backend.manager.data.permission.virtual_entity import (
    GovernCheckKey,
    OwnCheckKey,
)
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.permission import (
    RoleAlreadyAssigned,
    RoleNotAssigned,
    RoleNotFound,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.models.rbac_models.permission.scopes import PermissionOperationScope
from ai.backend.manager.models.rbac_models.permission.updaters import RolePermissionUpdater
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role.scopes import ScopedRoleOperationScope
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.specs.permission import PermissionEntry
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PermissionDBSource:
    _db: ExtendedAsyncSAEngine
    _ops: PermissionOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._ops = PermissionOpsProvider(db)

    # ------------------------------------------------------------------ role CRUD

    async def create_permission(
        self,
        role_id: RoleID,
        creator: RolePermissionCreator,
    ) -> PermissionData:
        """
        Create a permission entry of the named role.
        """
        async with self._ops.write_ops() as w:
            return await w.create_field(role_id, creator)

    async def delete_permission(
        self,
        purger: RolePermissionPurger,
    ) -> PermissionData:
        """
        Delete a permission entry.

        Raises:
            ObjectNotFound: If permission does not exist
        """
        async with self._ops.write_ops() as w:
            data = await w.purge_field_entity(purger)
            if data is None:
                raise ObjectNotFound(
                    f"Permission with ID {purger.target_id_value()} does not exist."
                )
            return data

    async def update_permission(
        self,
        updater: RolePermissionUpdater,
    ) -> PermissionData:
        """
        Update a permission entry.

        Raises:
            ObjectNotFound: If permission does not exist
        """
        async with self._ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise ObjectNotFound(
                    f"Permission with ID {updater.target_id_value()} does not exist."
                )
            return data

    async def _get_role(self, db_session: SASession, role_id: uuid.UUID) -> RoleRow:
        stmt = sa.select(RoleRow).where(RoleRow.id == role_id)
        role_row = await db_session.scalar(stmt)
        if role_row is None:
            raise RoleNotFound(f"Role with ID {role_id} does not exist.")
        return role_row

    # ============================================================
    # Private Helper Functions (for use within transactions)
    # ============================================================

    async def assign_role(self, data: UserRoleAssignmentInput) -> UserRoleRow:
        role_id = RoleID(data.role_id)
        async with self._ops.write_ops() as w:
            granted = await w.grant_roles(
                UserID(data.user_id),
                [role_id],
                None if data.granted_by is None else UserID(data.granted_by),
            )
        if not granted[0]:
            raise RoleAlreadyAssigned(
                f"Role {data.role_id} is already assigned to user {data.user_id}."
            )
        return await self._user_role_row(UserID(data.user_id), role_id)

    async def _user_role_row(self, user_id: UserID, role_id: RoleID) -> UserRoleRow:
        async with self._db.begin_readonly_session_read_committed() as read_sess:
            row = await read_sess.scalar(
                sa.select(UserRoleRow).where(
                    UserRoleRow.user_id == user_id,
                    UserRoleRow.role_id == role_id,
                )
            )
        if row is None:
            raise RoleNotAssigned(f"Role {role_id} is not assigned to user {user_id}.")
        return row

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

            # Used by PermissionControllerService.revoke_role() to decide whether to
            # take the user off the project's roster.
            project_subq = sa.select(RoleRow.scope_id).where(
                RoleRow.id == data.role_id,
                RoleRow.scope_type == ProjectEntityType(),
            )
            rows = (
                await db_session.execute(
                    sa.select(RoleRow.scope_id, sa.func.count(UserRoleRow.id))
                    .outerjoin(
                        UserRoleRow,
                        (UserRoleRow.role_id == RoleRow.id) & (UserRoleRow.user_id == data.user_id),
                    )
                    .where(
                        RoleRow.scope_type == ProjectEntityType(),
                        RoleRow.scope_id.in_(project_subq),
                    )
                    .group_by(RoleRow.scope_id)
                )
            ).all()

            return RoleRevocationResult(
                user_role_id=user_role_id,
                project_remaining_roles=[
                    ProjectRoleCount(project_id=r[0], remaining_count=r[1]) for r in rows
                ],
            )

    async def replace_role_permissions(
        self,
        role_id: RoleID,
        entries: Sequence[PermissionEntry],
    ) -> list[PermissionData]:
        """State the role's whole scoped-permission set; keys it held and the entries
        do not name are cleared. Answers the rows the role holds afterwards.

        Raises ``RoleNotFound`` if the role does not exist.
        """
        async with self._db.begin_readonly_session_read_committed() as read_sess:
            await self._get_role(read_sess, role_id)
        async with self._ops.write_ops() as w:
            await w.replace_permissions(role_id, entries)
        async with self._db.begin_readonly_session_read_committed() as read_sess:
            rows = (
                await read_sess.scalars(
                    sa.select(PermissionRow).where(PermissionRow.role_id == role_id)
                )
            ).all()
        return [row.to_data() for row in rows]

    async def get_role(self, role_id: uuid.UUID) -> RoleRow | None:
        async with self._db.begin_readonly_session_read_committed() as db_session:
            try:
                result = await self._get_role(db_session, role_id)
            except RoleNotFound:
                return None
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
        """Search the roles that sit in a given scope."""
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
                    id=ScopeId(scope_type=DomainEntityType(), scope_id=str(row.id)),
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
                    id=ScopeId(scope_type=ProjectEntityType(), scope_id=str(row.id)),
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
                    id=ScopeId(scope_type=UserEntityType(), scope_id=str(row.uuid)),
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

    # ------------------------------------------------ virtual-entity-chain checks

    async def owned_permissions(
        self,
        keys: Collection[OwnCheckKey],
    ) -> Mapping[OwnCheckKey, Permission]:
        """The bits each user holds on each entity; the walk is
        :meth:`PermissionReadOps.owned_permissions`."""
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
        self,
        role_id: RoleID,
        user_ids: Sequence[UserID],
        granted_by: UserID | None = None,
    ) -> list[UserRoleRow]:
        """Grant the role to each user; a user already holding it is left as it stands.
        Answers the rows the named users hold for the role afterwards."""
        async with self._ops.write_ops() as w:
            for user_id in user_ids:
                await w.grant_roles(user_id, [role_id], granted_by)
        async with self._db.begin_readonly_session_read_committed() as read_sess:
            rows = (
                await read_sess.scalars(
                    sa.select(UserRoleRow).where(
                        UserRoleRow.role_id == role_id,
                        UserRoleRow.user_id.in_(list(user_ids)),
                    )
                )
            ).all()
        return list(rows)

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
