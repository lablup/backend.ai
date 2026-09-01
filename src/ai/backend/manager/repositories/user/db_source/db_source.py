from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, NoReturn, cast
from uuid import UUID, uuid4

import aiotools
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, noload
from sqlalchemy.sql.expression import bindparam

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityRef, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.types import AccessKey, VFolderID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.common.bulk import BulkCreateFailure, BulkUpdateFailure
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import (
    KeyPairCreator,
    KeyPairData,
)
from ai.backend.manager.data.user.types import (
    BulkUserCreateResultData,
    BulkUserUpdateResultData,
    UserCreateResultData,
    UserData,
    UserSearchResult,
)
from ai.backend.manager.errors.keypair import NoDefaultKeypairResourcePolicy
from ai.backend.manager.errors.user import (
    KeyPairForbidden,
    KeyPairNotFound,
    UserConflict,
    UserModificationBadRequest,
    UserModificationFailure,
    UserNotFound,
    UserPurgeInProgress,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow, EndpointTokenRow
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    RESOURCE_USAGE_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.keypair.row import (
    KeyPairRow,
    generate_keypair_data,
    keypairs,
)
from ai.backend.manager.models.keypair.scopes import UserKeypairOperationScope
from ai.backend.manager.models.project import (
    ProjectRow,
    ProjectType,
)
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.resource_slot.aggregates import kernel_allocated_slots_expr
from ai.backend.manager.models.session import (
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
    QueryCondition,
    QueryOption,
    SessionRow,
    by_status,
    by_user_id,
)
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.types import join_by_related_field
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus, users
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.user.purgers import (
    UserErrorLogPurger,
    UserGroupAssociationPurger,
    UserKeyPairPurger,
    UserProjectRolePurger,
    UserPurger,
    UserScopeAssociationPurger,
    UserSessionGroupPurger,
    UserVFolderPermissionPurger,
)
from ai.backend.manager.models.user.scopes import (
    DomainUserOperationScope,
    ProjectUserOperationScope,
    RoleUserOperationScope,
)
from ai.backend.manager.models.user.updaters import UserUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderDeletionInfo,
    VFolderRow,
    VFolderStatusSet,
    vfolder_invitations,
    vfolder_permissions,
    vfolder_status_map,
    vfolders,
)
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.queries import user_scope_membership_query
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.ops.rbac.provider import (
    EntityMembersAddition,
    ScopeUserMember,
)
from ai.backend.manager.repositories.ops.user.provider import UserOpsProvider
from ai.backend.manager.repositories.ops.user.write import FullUserCreation, UserWriteOps
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.user.creators import (
    UserCreateSpec,
    UserScopeCreation,
)
from ai.backend.manager.repositories.vfolder.deletion import initiate_vfolder_deletion
from ai.backend.manager.secret.pool import KeyProviderPool

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserDBSource:
    """Database source for user-related operations."""

    _db: ExtendedAsyncSAEngine
    _v2_ops: V2DBOpsProvider
    _user_ops_provider: UserOpsProvider
    _key_provider_pool: KeyProviderPool

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        v2_ops_provider: V2DBOpsProvider,
        key_provider_pool: KeyProviderPool,
    ) -> None:
        self._db = db
        self._v2_ops = v2_ops_provider
        self._user_ops_provider = UserOpsProvider(db)
        self._key_provider_pool = key_provider_pool

    async def get_user_by_uuid(self, user_uuid: UUID) -> UserData:
        """
        Get user by UUID without ownership validation.
        Admin-only operation.
        """
        async with self._db.begin_readonly_session_read_committed() as db_session:
            user_row = await self._get_user_by_uuid(db_session, user_uuid)
            return user_row.to_data()

    async def get_by_email_validated(
        self,
        email: str,
    ) -> UserData:
        """
        Get user by email with ownership validation.
        Returns None if user not found or access denied.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            user_row = await self._get_user_by_email(session, email)
            return user_row.to_data()

    async def _default_keypair_resource_policy(self, session: SASession) -> str:
        """The name of the policy a keypair gets when nothing else names one."""
        name = await session.scalar(
            sa.select(KeyPairResourcePolicyRow.name).where(KeyPairResourcePolicyRow.is_default)
        )
        if name is None:
            raise NoDefaultKeypairResourcePolicy()
        return name

    async def create_user_validated(
        self, creator: UserCreator, group_ids: list[str] | None
    ) -> UserCreateResultData:
        """
        Create a new user with default keypair and group associations.
        """
        async with self._db.begin_readonly_session_read_committed() as session:
            policy = await self._default_keypair_resource_policy(session)
        async with self._user_ops_provider.write_ops() as w:
            return await self._create_user_with_keypair_and_groups(w, creator, group_ids, policy)

    async def _create_user_with_keypair_and_groups(
        self,
        w: UserWriteOps,
        creator: UserCreator,
        group_ids: list[str] | None,
        keypair_resource_policy: str,
    ) -> UserCreateResultData:
        """Provision a user (row, default keypair, domain/project/model-store scope
        enrollments) within the caller's write ops transaction."""
        duplicate_query = sa.select(UserRow.uuid).where(
            sa.or_(UserRow.email == creator.email, UserRow.username == creator.username)
        )
        duplicates = await w.batch_query_in_global(
            duplicate_query, BatchQuerier(pagination=NoPagination())
        )
        if duplicates.rows:
            raise UserConflict(
                f"User with email {creator.email} or username {creator.username} already exists."
            )

        result = await w.create_full_user(
            FullUserCreation(
                creation=UserScopeCreation(spec=creator),
                domain_id=creator.domain_id,
                project_ids=[ProjectID(UUID(gid)) for gid in group_ids or []],
                keypair_resource_policy=keypair_resource_policy,
                keypair_secrets=await generate_keypair_data(self._key_provider_pool),
            )
        )
        return UserCreateResultData(
            user=result.user_row.to_data(),
            keypair=result.keypair,
        )

    async def bulk_create_users_validated(
        self,
        items: list[UserCreateSpec],
    ) -> BulkUserCreateResultData:
        """Create multiple users with partial failure support.

        Each user is created in a savepoint - if one fails, others can still succeed.

        Args:
            items: List of UserCreateSpec for each user to create.
        """
        if not items:
            return BulkUserCreateResultData(successes=[], failures=[])

        successes: list[UserCreateResultData] = []
        failures: list[BulkCreateFailure] = []

        async with self._db.begin_readonly_session_read_committed() as session:
            policy = await self._default_keypair_resource_policy(session)
        async with self._user_ops_provider.write_ops() as w:
            for idx, item in enumerate(items):
                try:
                    async with w.savepoint():
                        successes.append(
                            await self._create_user_with_keypair_and_groups(
                                w, item.creator, item.group_ids, policy
                            )
                        )
                except Exception as e:
                    log.warning("Failed to create user {}: {}", item.creator.email, str(e))
                    failures.append(BulkCreateFailure(index=idx, exception=e))

        return BulkUserCreateResultData(successes=successes, failures=failures)

    async def bulk_update_users_validated(
        self,
        items: list[UserUpdater],
    ) -> BulkUserUpdateResultData:
        """Update multiple users with partial failure support.

        Each user is updated in a savepoint - if one fails, others can still succeed.

        Args:
            items: List of UserUpdater for each user to update.
        """
        if not items:
            return BulkUserUpdateResultData(successes=[], failures=[])

        successes: list[UserData] = []
        failures: list[BulkUpdateFailure] = []

        async with self._db.begin_session() as session:
            for idx, item in enumerate(items):
                try:
                    async with session.begin_nested():
                        updated_user = await self._update_single_user_validated(session, item)
                        successes.append(updated_user)
                except Exception as e:
                    log.warning("Failed to update user {}: {}", item.user_id, str(e))
                    failures.append(BulkUpdateFailure(index=idx, exception=e))

        return BulkUserUpdateResultData(successes=successes, failures=failures)

    async def _update_single_user_validated(
        self,
        session: SASession,
        updater: UserUpdater,
    ) -> UserData:
        """Update a single user with full validation, shared by the single and bulk paths."""
        user_id = updater.user_id
        to_update = updater.build_values()

        # Get current user data for validation (by UUID)
        current_user = await self._get_user_by_uuid_with_session(session, user_id)
        if current_user.status in UserStatus.purge_in_progress():
            raise UserPurgeInProgress(f"User is being purged: {user_id}")

        # Check if new username is already taken by another user
        new_username = updater.username.optional_value()
        if new_username and new_username != current_user.username:
            username_exists = await self._check_username_exists_for_other_user(
                session, username=new_username, exclude_email=current_user.email
            )
            if username_exists:
                raise UserModificationBadRequest(
                    f"Username '{new_username}' is already taken by another user."
                )

        # Check if new domain_name exists
        new_domain_name = updater.domain_name.optional_value()
        if new_domain_name and new_domain_name != current_user.domain_name:
            domain_exists = await self._check_domain_exists(session, new_domain_name)
            if not domain_exists:
                raise UserModificationBadRequest(f"Domain '{new_domain_name}' does not exist.")

        # Check if new resource_policy exists
        new_resource_policy = updater.resource_policy.optional_value()
        if new_resource_policy and new_resource_policy != current_user.resource_policy:
            policy_exists = await self._check_resource_policy_exists(session, new_resource_policy)
            if not policy_exists:
                raise UserModificationBadRequest(
                    f"Resource policy '{new_resource_policy}' does not exist."
                )

        # Update user
        if updater.password.optional_value():
            to_update["password_changed_at"] = sa.func.now()
        status = updater.status.optional_value()
        if status is not None and status != current_user.status:
            to_update["status_info"] = "admin-requested"
        update_query = (
            sa.update(users).where(users.c.uuid == user_id).values(to_update).returning(users)
        )
        result = await session.execute(update_query)
        updated_user = result.first()
        if not updated_user:
            raise UserModificationFailure("Failed to update user")

        # Handle role changes
        prev_role = current_user.role
        role = updater.role.optional_value()
        if role is not None and role != prev_role:
            await self._sync_keypair_roles(session, updated_user.uuid, role)

        # Handle group updates through the RBAC member ops in its own transaction.
        group_ids = updater.group_ids_value
        if group_ids is not None:
            await self._sync_user_project_memberships(
                updated_user.uuid, updated_user.domain_name, group_ids
            )
        return UserData.from_row(updated_user)

    async def update_user_by_uuid_validated(self, updater: UserUpdater) -> UserData:
        """Update user by UUID with validation and handle role/group changes."""
        async with self._db.begin_session() as session:
            return await self._update_single_user_validated(session, updater)

    async def delete_user_by_uuid_validated(self, user_uuid: UUID) -> None:
        """Soft delete a user by UUID, setting status to DELETED.

        The user's keypairs are left active: what keeps a deleted account out of the
        API is the status gate the auth middleware applies.
        """
        async with self._db.begin() as conn:
            result = await conn.execute(
                sa.update(users)
                .values(status=UserStatus.DELETED, status_info="admin-requested")
                .where(
                    (users.c.uuid == user_uuid)
                    & users.c.status.not_in(UserStatus.purge_in_progress())
                )
            )
            if result.rowcount == 0:
                await self._raise_missing_or_purging(conn, user_uuid)

    async def restore_user_by_uuid_validated(self, user_uuid: UUID) -> None:
        """Restore a soft-deleted user by UUID, setting status back to ACTIVE."""
        async with self._db.begin() as conn:
            result = await conn.execute(
                sa.update(users)
                .values(status=UserStatus.ACTIVE, status_info="admin-requested")
                .where(
                    (users.c.uuid == user_uuid)
                    & users.c.status.not_in(UserStatus.purge_in_progress())
                )
            )
            if result.rowcount == 0:
                await self._raise_missing_or_purging(conn, user_uuid)

    async def _raise_missing_or_purging(self, conn: AsyncConnection, user_uuid: UUID) -> NoReturn:
        """Name why a status write touched nothing: the row is gone, or a purge holds it."""
        current = await conn.scalar(sa.select(users.c.status).where(users.c.uuid == user_uuid))
        if current is None:
            raise UserNotFound(f"User with UUID {user_uuid} not found.")
        raise UserPurgeInProgress(f"User is being purged: {user_uuid}")

    async def purge_user_by_uuid(self, user_uuid: UUID) -> None:
        """Completely purge user and all associated data by UUID."""
        user_id = UserID(user_uuid)
        async with self._v2_ops.write_ops() as w:
            await w.batch_purge_field_entities(user_id, UserErrorLogPurger())
            await w.batch_purge_field_entities(user_id, UserKeyPairPurger())
            await w.batch_purge_field_entities(user_id, UserVFolderPermissionPurger())
            await w.batch_purge_field_entities(user_id, UserGroupAssociationPurger())
            # Placement groups the user still owns: their deployments were either
            # delegated (the groups moved with them) or deleted by now.
            await w.batch_purge_entities_in_global(UserSessionGroupPurger(user_id=user_id))
            await w.batch_purge_field_entities(user_id, UserScopeAssociationPurger())
            # Finally the user itself as a scope: the row and the RBAC graph it left.
            await w.purge_entity(UserPurger(user_id=user_id))

    async def check_user_vfolder_mounted_to_active_kernels(self, user_uuid: UUID) -> bool:
        """Check if user's vfolders are mounted to active kernels."""
        async with self._db.begin() as conn:
            return await self._user_vfolder_mounted_to_active_kernels(conn, user_uuid)

    async def migrate_shared_vfolders(
        self,
        deleted_user_uuid: UUID,
        target_user_uuid: UUID,
        target_user_email: str,
    ) -> int:
        """Migrate shared virtual folders ownership to target user."""
        async with self._db.begin() as conn:
            return await self._migrate_shared_vfolders(
                conn, deleted_user_uuid, target_user_uuid, target_user_email
            )

    async def retrieve_active_sessions(self, user_uuid: UUID) -> list[SessionRow]:
        """Retrieve active sessions for a user."""
        query_conditions: list[QueryCondition] = [
            by_user_id(user_uuid),
            by_status(AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES),
        ]

        query_options: list[QueryOption] = [
            join_by_related_field(SessionRow.user),
        ]

        return await SessionRow.list_session_by_condition(
            query_conditions, query_options, db=self._db
        )

    async def delegate_endpoint_ownership(
        self,
        user_uuid: UUID,
        target_user_uuid: UUID,
    ) -> None:
        """Delegate endpoint ownership to another user."""
        async with self._db.begin_session() as session:
            default_access_key = await session.scalar(
                sa.select(KeyPairRow.access_key).where(
                    (KeyPairRow.user == target_user_uuid) & KeyPairRow.is_default
                )
            )
            if default_access_key is None:
                raise KeyPairNotFound(
                    f"User {target_user_uuid} has no default keypair to delegate endpoints to."
                )
            await EndpointRow.delegate_endpoint_ownership(
                session, user_uuid, UserID(target_user_uuid), default_access_key
            )

    async def delete_endpoints(
        self,
        user_uuid: UUID,
        delete_destroyed_only: bool = False,
    ) -> None:
        """Delete user's endpoints."""
        async with self._db.begin_session() as session:
            await self._delete_endpoints(session, user_uuid, delete_destroyed_only)

    async def get_kernel_rows_for_monthly_stats(
        self,
        user_uuid: UUID | None,
    ) -> Sequence[Row[Any]]:
        """Fetch kernel rows for time-binned monthly stats."""
        now = datetime.now(tzutc())
        start_date = now - timedelta(days=30)

        async with self._db.begin_readonly() as conn:
            query = (
                sa.select(
                    kernels.c.id,
                    kernels.c.created_at,
                    kernels.c.terminated_at,
                    kernel_allocated_slots_expr(kernels.c.id).label("occupied_slots"),
                )
                .select_from(kernels)
                .where(
                    (kernels.c.terminated_at >= start_date)
                    & (kernels.c.status.in_(RESOURCE_USAGE_KERNEL_STATUSES)),
                )
                .order_by(sa.asc(kernels.c.created_at))
            )
            if user_uuid is not None:
                query = query.where(kernels.c.user_uuid == user_uuid)
            result = await conn.execute(query)
            return result.fetchall()

    async def delete_vfolders(
        self,
        user_uuid: UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """
        Delete user's all virtual folders as well as their physical data.
        """
        target_vfs: list[VFolderDeletionInfo] = []
        async with self._db.begin_session() as db_session:
            await db_session.execute(
                vfolder_permissions.delete().where(vfolder_permissions.c.user == user_uuid),
            )
            result = await db_session.scalars(
                sa.select(VFolderRow).where(
                    sa.and_(
                        VFolderRow.user == user_uuid,
                        VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.OWNER_PURGABLE]),
                    )
                ),
            )
            rows = result.fetchall()
            for vf in rows:
                target_vfs.append(
                    VFolderDeletionInfo(VFolderID.from_row(vf), vf.host, vf.unmanaged_path)
                )

        storage_ptask_group = aiotools.PersistentTaskGroup()
        await initiate_vfolder_deletion(
            self._db,
            self._v2_ops,
            target_vfs,
            storage_manager,
            storage_ptask_group,
        )

        return len(target_vfs)

    async def delete_keypairs_with_valkey(
        self,
        user_uuid: UUID,
        valkey_stat_client: ValkeyStatClient,
    ) -> int:
        """
        Delete user's all keypairs with Valkey cleanup.
        """
        async with self._db.begin() as conn:
            result = await conn.execute(
                sa.delete(keypairs).where(keypairs.c.user == user_uuid),
            )
            return result.rowcount

    async def _check_domain_exists(
        self, session: SASession | AsyncConnection, domain_name: str
    ) -> bool:
        query = sa.select(DomainRow.name).where(DomainRow.name == domain_name)
        result = await session.scalar(query)
        return result is not None

    async def _check_resource_policy_exists(
        self, session: SASession | AsyncConnection, policy_name: str
    ) -> bool:
        """Check if the resource policy exists."""
        query = sa.select(UserResourcePolicyRow.name).where(
            UserResourcePolicyRow.name == policy_name
        )
        result = await session.scalar(query)
        return result is not None

    async def _check_username_exists_for_other_user(
        self, session: SASession, *, username: str, exclude_email: str
    ) -> bool:
        """Check if the username is already taken by another user."""
        query = sa.select(UserRow.uuid).where(
            sa.and_(UserRow.username == username, UserRow.email != exclude_email)
        )
        result = await session.scalar(query)
        return result is not None

    async def _get_user_by_email(self, session: SASession, email: str) -> UserRow:
        """Private method to get user by email."""
        res = await session.scalar(
            sa.select(UserRow)
            .where(UserRow.email == email)
            .options(joinedload(UserRow.default_keypair))
        )
        if res is None:
            raise UserNotFound(f"User with email {email} not found.")
        return res

    async def _get_user_by_uuid(self, session: SASession, user_uuid: UUID) -> UserRow:
        """Private method to get user by UUID."""
        res = await session.scalar(
            sa.select(UserRow)
            .where(UserRow.uuid == user_uuid)
            .options(joinedload(UserRow.default_keypair))
        )
        if res is None:
            raise UserNotFound(f"User with UUID {user_uuid} not found.")
        return res

    async def _get_user_by_uuid_with_session(self, session: SASession, user_uuid: UUID) -> UserRow:
        """Private method to get user by UUID using a session.

        Uses a Core-level select on the ``users`` table so that the returned row exposes
        column attributes without requiring ORM mapping. Callers treat the result as a
        read-only snapshot.
        """
        result = await session.execute(sa.select(users).where(users.c.uuid == user_uuid))
        res = result.first()
        if res is None:
            raise UserNotFound(f"User with UUID {user_uuid} not found.")
        return cast(UserRow, res)

    async def _switch_default_keypair(
        self, session: SASession, user_id: UserID, access_key: str
    ) -> None:
        """Move the default marker onto ``access_key``, which must still be an active
        key of the user.

        Clearing the previous marker needs its own statement: a partial unique index
        allows a user only one marked keypair.
        """
        await session.execute(
            sa.update(KeyPairRow)
            .where((KeyPairRow.user == user_id) & KeyPairRow.is_default)
            .values(is_default=False)
        )
        switched = await session.scalar(
            sa.update(KeyPairRow)
            .where(
                (KeyPairRow.user == user_id)
                & (KeyPairRow.access_key == access_key)
                & KeyPairRow.is_active
            )
            .values(is_default=True)
            .returning(KeyPairRow.access_key)
        )
        if switched is None:
            # The target stopped being an active key of the user between the two
            # statements; the same transaction carries the cleared marker back.
            raise KeyPairForbidden("The access key is no longer an active key of this user.")

    async def _sync_keypair_roles(
        self, session: SASession, user_uuid: UUID, new_role: UserRole
    ) -> None:
        """Private method to sync keypair roles with user role."""
        result = await session.execute(
            sa.select(
                keypairs.c.user,
                keypairs.c.is_active,
                keypairs.c.is_admin,
                keypairs.c.access_key,
            )
            .select_from(keypairs)
            .where(keypairs.c.user == user_uuid)
            .order_by(sa.desc(keypairs.c.is_admin))
            .order_by(sa.desc(keypairs.c.is_active))
        )

        if new_role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            # User becomes admin - set first keypair as active admin
            kp = result.first()
            if kp is None:
                return
            kp_data = {}
            if not kp.is_admin:
                kp_data["is_admin"] = True
            if not kp.is_active:
                kp_data["is_active"] = True
            if kp_data:
                await session.execute(
                    sa.update(keypairs).values(kp_data).where(keypairs.c.user == user_uuid)
                )
        else:
            # User becomes non-admin - update keypairs accordingly
            rows = result.fetchall()
            kp_updates = []
            for idx, row in enumerate(rows):
                kp_data = {
                    "b_access_key": row.access_key,
                    "is_admin": row.is_admin,
                    "is_active": row.is_active,
                }
                if idx == 0:
                    kp_data["is_admin"] = False
                    kp_updates.append(kp_data)
                    continue
                if row.is_admin and row.is_active:
                    kp_data["is_active"] = False
                    kp_updates.append(kp_data)

            if kp_updates:
                await session.execute(
                    sa.update(keypairs)
                    .values({
                        "is_admin": bindparam("is_admin"),
                        "is_active": bindparam("is_active"),
                    })
                    .where(keypairs.c.access_key == bindparam("b_access_key")),
                    kp_updates,
                )

    async def _sync_user_project_memberships(
        self,
        user_uuid: UUID,
        domain_name: str,
        group_ids: list[str],
    ) -> None:
        """Sync the user's project memberships to match ``group_ids`` (the domain's
        model-store projects always included) through the RBAC member ops, in its
        own transaction.

        Diff-based: only projects entering or leaving the target set are touched,
        preserving existing rows for unchanged memberships. Joining a project
        grants its ``auto_assign`` roles; member ops leave role mappings untouched
        on removal, so the roles of the projects left behind are revoked afterwards,
        in a v2 transaction of their own.
        """
        member_ref = EntityRef(entity_type=USER_ENTITY_TYPE, entity_id=UserID(user_uuid))
        left_project_ids: list[ProjectID] = []
        async with self._user_ops_provider.write_ops() as w:
            target_result = await w.batch_query_in_global(
                sa.select(ProjectRow.id).where(
                    ProjectRow.domain_name == domain_name,
                    sa.or_(
                        ProjectRow.id.in_([UUID(gid) for gid in group_ids]),
                        ProjectRow.type == ProjectType.MODEL_STORE,
                    ),
                ),
                BatchQuerier(pagination=NoPagination()),
            )
            target_project_ids = {row.id for row in target_result.rows}

            current_result = await w.batch_query_in_global(
                user_scope_membership_query(PROJECT_SCOPE_TYPE).where(
                    EntityMembershipRow.entity_id == user_uuid
                ),
                BatchQuerier(pagination=NoPagination()),
            )
            current_project_ids = {row.scope_id for row in current_result.rows}

            for project_id in current_project_ids - target_project_ids:
                await w.remove_bulk_members(
                    ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(project_id)),
                    [member_ref],
                )
                left_project_ids.append(ProjectID(project_id))
            for project_id in target_project_ids - current_project_ids:
                project_scope = ScopeRef(
                    scope_type=PROJECT_SCOPE_TYPE, scope_id=ProjectID(project_id)
                )
                await w.ensure_scope(project_scope)
                await w.add_bulk_members(
                    EntityMembersAddition(
                        scope=project_scope,
                        members=[ScopeUserMember(user_id=UserID(user_uuid))],
                    )
                )

        if left_project_ids:
            async with self._v2_ops.write_ops() as v2:
                for project_id in left_project_ids:
                    await v2.batch_purge_field_entities(
                        UserID(user_uuid), UserProjectRolePurger(project_id=project_id)
                    )

    async def _get_user_uuid_by_email_with_conn(self, conn: AsyncConnection, email: str) -> UUID:
        """Get user UUID by email using an existing connection."""
        result = await conn.execute(sa.select(users.c.uuid).where(users.c.email == email))
        row = result.first()
        if not row:
            raise UserNotFound()
        return cast(UUID, row.uuid)

    async def _user_vfolder_mounted_to_active_kernels(
        self,
        conn: AsyncConnection,
        user_uuid: UUID,
    ) -> bool:
        """
        Check if no active kernel is using the user's virtual folders.
        """
        result = await conn.execute(
            sa.select(vfolders.c.id).select_from(vfolders).where(vfolders.c.user == user_uuid),
        )
        rows = result.fetchall()
        user_vfolder_ids = [row.id for row in rows]
        query = (
            sa.select(kernels.c.mounts)
            .select_from(kernels)
            .where(kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
        )
        async for row in await conn.stream(query):
            for _mount in row.mounts:
                try:
                    vfolder_id = UUID(_mount[2])
                    if vfolder_id in user_vfolder_ids:
                        return True
                except Exception:
                    pass
        return False

    async def _migrate_shared_vfolders(
        self,
        conn: AsyncConnection,
        deleted_user_uuid: UUID,
        target_user_uuid: UUID,
        target_user_email: str,
    ) -> int:
        """
        Migrate shared virtual folders' ownership to a target user.
        If migrating virtual folder's name collides with target user's already
        existing folder, append random string to the migrating one.
        """
        # Gather target user's virtual folders' names.
        query = (
            sa.select(vfolders.c.name)
            .select_from(vfolders)
            .where(vfolders.c.user == target_user_uuid)
        )
        existing_vfolder_names = [row.name async for row in (await conn.stream(query))]

        # Migrate shared virtual folders.
        # If virtual folder's name collides with target user's folder,
        # append random string to the name of the migrating folder.
        j = vfolder_permissions.join(
            vfolders,
            vfolder_permissions.c.vfolder == vfolders.c.id,
        )
        query = (
            sa.select(vfolders.c.id, vfolders.c.name)
            .select_from(j)
            .where(vfolders.c.user == deleted_user_uuid)
        )
        migrate_updates = []
        async for row in await conn.stream(query):
            name = row.name
            if name in existing_vfolder_names:
                name += f"-{uuid4().hex[:10]}"
            migrate_updates.append({"vid": row.id, "vname": name})

        if migrate_updates:
            # Remove invitations and vfolder_permissions from target user.
            # Target user will be the new owner, and it does not make sense to have
            # invitation and shared permission for its own folder.
            migrate_vfolder_ids = [item["vid"] for item in migrate_updates]
            delete_query = sa.delete(vfolder_invitations).where(
                (vfolder_invitations.c.invitee == target_user_email)
                & (vfolder_invitations.c.vfolder.in_(migrate_vfolder_ids))
            )
            await conn.execute(delete_query)
            delete_query = sa.delete(vfolder_permissions).where(
                (vfolder_permissions.c.user == target_user_uuid)
                & (vfolder_permissions.c.vfolder.in_(migrate_vfolder_ids))
            )
            await conn.execute(delete_query)

            rowcount = 0
            for item in migrate_updates:
                update_query = (
                    sa.update(vfolders)
                    .values(
                        user=target_user_uuid,
                        name=item["vname"],
                    )
                    .where(vfolders.c.id == item["vid"])
                )
                result = await conn.execute(update_query)
                rowcount += result.rowcount
            return rowcount
        return 0

    async def _delete_endpoints(
        self,
        session: SASession,
        user_uuid: UUID,
        delete_destroyed_only: bool = False,
    ) -> None:
        """Private method to delete user's endpoints."""
        if delete_destroyed_only:
            status_filter = {EndpointLifecycle.DESTROYED}
        else:
            status_filter = {status for status in EndpointLifecycle}

        endpoint_rows = await EndpointRow.list_endpoint(
            session, user_uuid=user_uuid, load_tokens=True, status_filter=status_filter
        )

        token_ids_to_delete = []
        endpoint_ids_to_delete = []
        for row in endpoint_rows:
            token_ids_to_delete.extend([token.id for token in row.tokens])
            endpoint_ids_to_delete.append(row.id)

        if token_ids_to_delete:
            await session.execute(
                sa.delete(EndpointTokenRow).where(EndpointTokenRow.id.in_(token_ids_to_delete))
            )

        if endpoint_ids_to_delete:
            await session.execute(
                sa.delete(EndpointRow).where(EndpointRow.id.in_(endpoint_ids_to_delete))
            )

    # ==================== Search Methods ====================

    async def search_users(
        self,
        querier: BatchQuerier,
    ) -> UserSearchResult:
        """Search all users with pagination and filters (admin only).

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            UserSearchResult with matching users and pagination info.
        """
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(UserRow).options(joinedload(UserRow.default_keypair))
            result = await execute_batch_querier(db_session, query, querier)

            items = [row.UserRow.to_data() for row in result.rows]
            return UserSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_users_by_domain(
        self,
        scope: DomainUserOperationScope,
        querier: BatchQuerier,
    ) -> UserSearchResult:
        """Search users within a domain.

        Args:
            scope: DomainUserOperationScope defining the domain to search within.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            UserSearchResult with matching users and pagination info.
        """
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(UserRow).options(joinedload(UserRow.default_keypair))
            result = await execute_batch_querier(db_session, query, querier, scopes=[scope])

            items = [row.UserRow.to_data() for row in result.rows]
            return UserSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_users_by_project(
        self,
        scope: ProjectUserOperationScope,
        querier: BatchQuerier,
    ) -> UserSearchResult:
        """Search users within a project.

        Membership comes from the project's virtual scope; the scope supplies
        the membership predicate.

        Args:
            scope: ProjectUserOperationScope defining the project to search within.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            UserSearchResult with matching users and pagination info.
        """
        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(UserRow).select_from(UserRow).options(joinedload(UserRow.default_keypair))
            )
            result = await execute_batch_querier(db_session, query, querier, scopes=[scope])

            items = [row.UserRow.to_data() for row in result.rows]
            return UserSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_users_by_role(
        self,
        scope: RoleUserOperationScope,
        querier: BatchQuerier,
    ) -> UserSearchResult:
        """Search users assigned to a role.

        Joins with user_roles to find users assigned to the role.
        """
        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(UserRow)
                .select_from(UserRow)
                .join(
                    UserRoleRow,
                    UserRow.uuid == UserRoleRow.user_id,
                )
                .options(joinedload(UserRow.default_keypair))
            )
            result = await execute_batch_querier(db_session, query, querier, scopes=[scope])

            items = [row.UserRow.to_data() for row in result.rows]
            return UserSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def keypair_settings_to_inherit(self, user_uuid: UUID) -> KeyPairCreator:
        """The settings a newly issued keypair takes from the user's default keypair,
        falling back to the marked resource policy when they have none."""
        async with self._db.begin_readonly_session() as session:
            default_kp_row = (
                await session.scalars(
                    sa.select(KeyPairRow)
                    .where((KeyPairRow.user == user_uuid) & KeyPairRow.is_default)
                    .options(noload("*"))
                )
            ).first()
            if default_kp_row is None:
                return KeyPairCreator(
                    is_active=True,
                    is_admin=False,
                    resource_policy=await self._default_keypair_resource_policy(session),
                )
            return KeyPairCreator(
                is_active=True,
                is_admin=default_kp_row.is_admin,
                resource_policy=default_kp_row.resource_policy,
                rate_limit=default_kp_row.rate_limit,
            )

    async def switch_default_access_key(self, user_id: UserID, access_key: AccessKey) -> None:
        """Move the ``is_default`` marker among the user's keypairs onto ``access_key``."""
        async with self._db.begin_session() as session:
            kp_row = (
                await session.scalars(
                    sa.select(KeyPairRow)
                    .where(KeyPairRow.access_key == access_key)
                    .options(
                        load_only(
                            KeyPairRow.access_key,
                            KeyPairRow.user,
                            KeyPairRow.is_active,
                            KeyPairRow.is_default,
                        ),
                    )
                )
            ).first()
            if not kp_row:
                raise KeyPairNotFound(
                    "Cannot set a non-existing access key as the default access key."
                )
            if kp_row.user != user_id:
                raise KeyPairForbidden(
                    "Cannot set another user's access key as the default access key."
                )
            if not kp_row.is_active:
                raise KeyPairForbidden("Cannot set an inactive keypair as the default access key.")

            await self._switch_default_keypair(session, user_id, access_key)

    async def search_my_keypairs(
        self,
        scope: UserKeypairOperationScope,
        querier: BatchQuerier,
    ) -> SearchResult[KeyPairData]:
        """Search keypairs owned by the scoped user.

        Args:
            scope: Search scope containing the user UUID whose keypairs to retrieve.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            SearchResult with matching keypairs and pagination info.
        """
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(KeyPairRow)
            result = await execute_batch_querier(db_session, query, querier, scopes=[scope])
            items = [row.KeyPairRow.to_data() for row in result.rows]
            return SearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def admin_search_keypairs(
        self,
        querier: BatchQuerier,
    ) -> SearchResult[KeyPairData]:
        """Admin search all keypairs without scope restriction."""
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(KeyPairRow)
            result = await execute_batch_querier(db_session, query, querier)
            items = [row.KeyPairRow.to_data() for row in result.rows]
            return SearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def keypair(self, keypair_id: KeyPairID) -> KeyPairData:
        """Read one keypair by its id."""
        async with self._db.begin_readonly_session() as db_session:
            kp_row = (
                await db_session.scalars(
                    sa.select(KeyPairRow).where(KeyPairRow.id == keypair_id).options(noload("*"))
                )
            ).first()
            if not kp_row:
                raise KeyPairNotFound(f"Keypair {keypair_id} not found")
            return kp_row.to_data()

    async def admin_get_keypair(self, access_key: str) -> KeyPairData:
        """Admin retrieves a single keypair by access key."""
        async with self._db.begin_readonly_session() as db_session:
            kp_row = (
                await db_session.scalars(
                    sa.select(KeyPairRow)
                    .where(KeyPairRow.access_key == access_key)
                    .options(noload("*"))
                )
            ).first()
            if not kp_row:
                raise KeyPairNotFound(f"Keypair {access_key} not found")
            return kp_row.to_data()

    async def admin_update_ssh_keypair(
        self,
        access_key: str,
        ssh_public_key: str,
        ssh_private_key: str,
    ) -> None:
        """Admin registers (overwrites) a user's SSH keypair."""
        async with self._db.begin_session() as session:
            exists = (
                await session.scalars(
                    sa.select(KeyPairRow.access_key).where(KeyPairRow.access_key == access_key)
                )
            ).first()
            if exists is None:
                raise KeyPairNotFound(f"Keypair {access_key} not found")
            await session.execute(
                sa.update(keypairs)
                .where(keypairs.c.access_key == access_key)
                .values(
                    ssh_public_key=ssh_public_key,
                    ssh_private_key=ssh_private_key,
                )
            )

    async def admin_clear_ssh_keypair(self, access_key: str) -> None:
        """Admin clears a user's SSH keypair."""
        async with self._db.begin_session() as session:
            exists = (
                await session.scalars(
                    sa.select(KeyPairRow.access_key).where(KeyPairRow.access_key == access_key)
                )
            ).first()
            if exists is None:
                raise KeyPairNotFound(f"Keypair {access_key} not found")
            await session.execute(
                sa.update(keypairs)
                .where(keypairs.c.access_key == access_key)
                .values(
                    ssh_public_key=None,
                    ssh_private_key=None,
                )
            )

    async def admin_get_ssh_public_key(self, access_key: str) -> str | None:
        """Admin retrieves a user's SSH public key."""
        async with self._db.begin_readonly_session() as db_session:
            exists = (
                await db_session.scalars(
                    sa.select(KeyPairRow.access_key).where(KeyPairRow.access_key == access_key)
                )
            ).first()
            if exists is None:
                raise KeyPairNotFound(f"Keypair {access_key} not found")
            ssh_public_key: str | None = (
                await db_session.scalars(
                    sa.select(KeyPairRow.ssh_public_key).where(KeyPairRow.access_key == access_key)
                )
            ).first()
            return ssh_public_key
