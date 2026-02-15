from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, cast
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
from ai.backend.common.types import AccessKey, VFolderID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.keypair.types import KeyPairCreator
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.user.types import (
    BulkUserCreateResultData,
    UserCreateResultData,
    UserData,
    UserSearchResult,
)
from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT, DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.errors.user import (
    KeyPairForbidden,
    KeyPairNotFound,
    UserConflict,
    UserCreationBadRequest,
    UserCreationFailure,
    UserModificationBadRequest,
    UserModificationFailure,
    UserNotFound,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointLifecycle, EndpointRow, EndpointTokenRow
from ai.backend.manager.models.group import (
    AssocGroupUserRow,
    ProjectType,
    association_groups_users,
    groups,
)
from ai.backend.manager.models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    RESOURCE_USAGE_KERNEL_STATUSES,
    kernels,
)
from ai.backend.manager.models.keypair import KeyPairRow, generate_keypair_data, keypairs
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.session import (
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
    QueryCondition,
    QueryOption,
    SessionRow,
    by_status,
    by_user_id,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.types import join_by_related_field
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderDeletionInfo,
    VFolderRow,
    VFolderStatusSet,
    initiate_vfolder_deletion,
    vfolder_invitations,
    vfolder_permissions,
    vfolder_status_map,
    vfolders,
)
from ai.backend.manager.repositories.base.creator import BulkCreatorError, Creator, execute_creator
from ai.backend.manager.repositories.base.purger import execute_batch_purger
from ai.backend.manager.repositories.base.querier import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import (
    AssociationScopesEntitiesCreatorSpec,
    UserRoleCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.purgers import (
    create_user_error_log_purger,
    create_user_group_association_purger,
    create_user_keypair_purger,
    create_user_purger,
    create_user_vfolder_permission_purger,
)
from ai.backend.manager.repositories.user.types import DomainUserSearchScope, ProjectUserSearchScope
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.services.user.actions.create_user import UserCreateSpec

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UserDBSource:
    """Database source for user-related operations."""

    _db: ExtendedAsyncSAEngine
    _role_manager: RoleManager

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._role_manager = RoleManager()

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
            return UserData.from_row(user_row)

    async def create_user_validated(
        self, creator: Creator[UserRow], group_ids: list[str] | None
    ) -> UserCreateResultData:
        """
        Create a new user with default keypair and group associations.
        """
        spec = cast(UserCreatorSpec, creator.spec)
        domain_name = spec.domain_name
        email = spec.email
        user_name = spec.username

        async with self._db.begin_session() as db_session:
            # Check if domain exists before creating user
            domain_exists = await self._check_domain_exists(db_session, domain_name)
            if not domain_exists:
                raise UserCreationBadRequest(f"Domain '{domain_name}' does not exist.")

            # Check if user with the same email or username already exists
            duplicate_exists = await self._check_user_exists_with_email_or_username(
                db_session, email=email, username=user_name
            )
            if duplicate_exists:
                raise UserConflict(
                    f"User with email {email} or username {user_name} already exists."
                )
            # Insert user (integrity_error_checks on UserCreatorSpec handles constraint violations)
            result = await execute_creator(db_session, creator)
            row = result.row

            if not row:
                raise UserCreationFailure("Failed to create user")
            created_user = row.to_data()

            # Create default keypair
            email = created_user.email
            keypair_creator = KeyPairCreator(
                is_active=(created_user.status == UserStatus.ACTIVE),
                is_admin=created_user.role in ["superadmin", "admin"],
                resource_policy=DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME,
                rate_limit=DEFAULT_KEYPAIR_RATE_LIMIT,
            )
            generated = generate_keypair_data()
            kp_row = KeyPairRow.from_creator(keypair_creator, generated, created_user.id, email)
            db_session.add(kp_row)
            await db_session.flush()
            await db_session.refresh(kp_row)
            kp_data = kp_row.to_data()

            # Update user main_access_key
            row.main_access_key = kp_data.access_key
            created_user.main_access_key = kp_data.access_key

            # Add user to groups including model store project
            if created_user.domain_name:
                await self._add_user_to_groups(
                    db_session, created_user.uuid, created_user.domain_name, group_ids or []
                )

            role = await self._role_manager.create_system_role(db_session, created_user)
            user_role_creator = Creator(
                spec=UserRoleCreatorSpec(user_id=created_user.uuid, role_id=role.id)
            )
            await self._role_manager.map_user_to_role(db_session, user_role_creator)
            entity_scope_creator = Creator(
                spec=AssociationScopesEntitiesCreatorSpec(
                    scope_id=ScopeId(ScopeType.DOMAIN, str(created_user.domain_name)),
                    object_id=ObjectId(EntityType.USER, str(created_user.uuid)),
                )
            )
            await self._role_manager.map_entity_to_scope(db_session, entity_scope_creator)

        return UserCreateResultData(created_user, kp_data)

    async def _create_single_user_with_keypair_and_groups(
        self,
        db_session: SASession,
        item: UserCreateSpec,
    ) -> UserData:
        """Create a single user with keypair, group assignments, and role mappings.

        This is a helper method used by bulk_create_users_validated to create
        each individual user within a savepoint.

        Args:
            db_session: The database session to use.
            item: The user creation specification including group assignments.

        Returns:
            The created user data.

        Raises:
            UserCreationBadRequest: If the domain does not exist.
            UserConflict: If email or username already exists.
            UserCreationFailure: If user creation fails.
        """
        spec = cast(UserCreatorSpec, item.creator.spec)

        # Validate domain
        if not await self._check_domain_exists(db_session, spec.domain_name):
            raise UserCreationBadRequest(f"Domain '{spec.domain_name}' does not exist")

        # Validate no duplicate
        if await self._check_user_exists_with_email_or_username(
            db_session, email=spec.email, username=spec.username
        ):
            raise UserConflict(f"Email '{spec.email}' or username '{spec.username}' already exists")

        # Create user
        result = await execute_creator(db_session, item.creator)
        row = result.row
        if not row:
            raise UserCreationFailure(f"Failed to create user {spec.email}")

        created_user = row.to_data()

        # Create default keypair
        keypair_creator = KeyPairCreator(
            is_active=(created_user.status == UserStatus.ACTIVE),
            is_admin=created_user.role in ["superadmin", "admin"],
            resource_policy=DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME,
            rate_limit=DEFAULT_KEYPAIR_RATE_LIMIT,
        )
        generated = generate_keypair_data()
        kp_row = KeyPairRow.from_creator(
            keypair_creator, generated, created_user.id, created_user.email
        )
        db_session.add(kp_row)
        await db_session.flush()
        kp_data = kp_row.to_data()

        # Update user main_access_key
        row.main_access_key = kp_data.access_key
        created_user.main_access_key = kp_data.access_key

        # Add user to groups
        if created_user.domain_name:
            await self._add_user_to_groups(
                db_session,
                created_user.uuid,
                created_user.domain_name,
                item.group_ids or [],
            )

        # Create system role and mappings
        role = await self._role_manager.create_system_role(db_session, created_user)
        user_role_creator = Creator(
            spec=UserRoleCreatorSpec(user_id=created_user.uuid, role_id=role.id)
        )
        await self._role_manager.map_user_to_role(db_session, user_role_creator)
        entity_scope_creator = Creator(
            spec=AssociationScopesEntitiesCreatorSpec(
                scope_id=ScopeId(ScopeType.DOMAIN, str(created_user.domain_name)),
                object_id=ObjectId(EntityType.USER, str(created_user.uuid)),
            )
        )
        await self._role_manager.map_entity_to_scope(db_session, entity_scope_creator)

        return created_user

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

        successes: list[UserData] = []
        failures: list[BulkCreatorError[UserRow]] = []

        async with self._db.begin_session() as db_session:
            for idx, item in enumerate(items):
                spec = cast(UserCreatorSpec, item.creator.spec)
                try:
                    async with db_session.begin_nested():
                        created_user = await self._create_single_user_with_keypair_and_groups(
                            db_session, item
                        )
                        successes.append(created_user)
                except Exception as e:
                    log.warning("Failed to create user {}: {}", spec.email, str(e))
                    failures.append(BulkCreatorError(spec=spec, exception=e, index=idx))

        return BulkUserCreateResultData(successes=successes, failures=failures)

    async def update_user_validated(
        self,
        email: str,
        updater: Updater[UserRow],
    ) -> UserData:
        """
        Update user with ownership validation and handle role/group changes.
        """
        updater_spec = cast(UserUpdaterSpec, updater.spec)
        to_update = updater_spec.build_values()
        async with self._db.begin() as conn:
            # Get current user data for validation
            current_user = await self._get_user_by_email_with_conn(conn, email)

            # Check if new username is already taken by another user
            new_username = updater_spec.username.optional_value()
            if new_username and new_username != current_user.username:
                username_exists = await self._check_username_exists_for_other_user(
                    conn, username=new_username, exclude_email=email
                )
                if username_exists:
                    raise UserModificationBadRequest(
                        f"Username '{new_username}' is already taken by another user."
                    )

            # Check if new domain_name exists
            new_domain_name = updater_spec.domain_name.optional_value()
            if new_domain_name and new_domain_name != current_user.domain_name:
                domain_exists = await self._check_domain_exists(conn, new_domain_name)
                if not domain_exists:
                    raise UserModificationBadRequest(f"Domain '{new_domain_name}' does not exist.")

            # Check if new resource_policy exists
            new_resource_policy = updater_spec.resource_policy.optional_value()
            if new_resource_policy and new_resource_policy != current_user.resource_policy:
                policy_exists = await self._check_resource_policy_exists(conn, new_resource_policy)
                if not policy_exists:
                    raise UserModificationBadRequest(
                        f"Resource policy '{new_resource_policy}' does not exist."
                    )

            # Handle main_access_key validation
            main_access_key = updater_spec.main_access_key.optional_value()
            if main_access_key:
                await self._validate_and_update_main_access_key(conn, email, main_access_key)

            # Update user
            if updater_spec.password.optional_value():
                to_update["password_changed_at"] = sa.func.now()
            status = updater_spec.status.optional_value()
            if status is not None and status != current_user.status:
                to_update["status_info"] = "admin-requested"
            update_query = (
                sa.update(users).where(users.c.email == email).values(to_update).returning(users)
            )
            result = await conn.execute(update_query)
            updated_user = result.first()
            if not updated_user:
                raise UserModificationFailure("Failed to update user")

            # Handle role changes
            prev_role = current_user.role
            role = updater_spec.role.optional_value()
            if role is not None and role != prev_role:
                await self._sync_keypair_roles(conn, updated_user.uuid, role)

            # Handle group updates
            group_ids = updater_spec.group_ids_value
            if group_ids is not None:
                await self._update_user_groups(
                    conn, updated_user.uuid, updated_user.domain_name, group_ids
                )
            return UserData.from_row(updated_user)

    async def soft_delete_user_validated(self, email: str) -> None:
        """
        Soft delete user by setting status to DELETED and deactivating keypairs.
        """
        async with self._db.begin() as conn:
            # Deactivate all user keypairs
            await conn.execute(
                sa.update(keypairs).values(is_active=False).where(keypairs.c.user_id == email)
            )
            # Soft delete user
            await conn.execute(
                sa.update(users)
                .values(status=UserStatus.DELETED, status_info="admin-requested")
                .where(users.c.email == email)
            )

    async def purge_user(self, email: str) -> None:
        """Completely purge user and all associated data."""
        async with self._db.begin_session() as session:
            user_uuid = await self._get_user_uuid_by_email(session, email)

            # Delete all user data in proper order using purger pattern
            await execute_batch_purger(session, create_user_error_log_purger(user_uuid))
            await execute_batch_purger(session, create_user_keypair_purger(user_uuid))
            await execute_batch_purger(session, create_user_vfolder_permission_purger(user_uuid))
            await execute_batch_purger(session, create_user_group_association_purger(user_uuid))

            # Finally delete the user
            await execute_batch_purger(session, create_user_purger(user_uuid))

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
        target_main_access_key: AccessKey,
    ) -> None:
        """Delegate endpoint ownership to another user."""
        async with self._db.begin_session() as session:
            await EndpointRow.delegate_endpoint_ownership(
                session, user_uuid, target_user_uuid, target_main_access_key
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
                    kernels.c.occupied_slots,
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
                        VFolderRow.status.in_(vfolder_status_map[VFolderStatusSet.DELETABLE]),
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
            ak_rows = await conn.execute(
                sa.select(keypairs.c.access_key).where(keypairs.c.user == user_uuid),
            )
            if (row := ak_rows.first()) and (access_key := row.access_key):
                # Log concurrency used only when there is at least one keypair.
                await valkey_stat_client.delete_keypair_concurrency(
                    access_key=access_key,
                    is_private=False,
                )
                await valkey_stat_client.delete_keypair_concurrency(
                    access_key=access_key,
                    is_private=True,
                )
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

    async def _check_user_exists_with_email_or_username(
        self, session: SASession, *, email: str, username: str
    ) -> bool:
        query = sa.select(UserRow.uuid).where(
            sa.or_(UserRow.email == email, UserRow.username == username)
        )
        result = await session.scalar(query)
        return result is not None

    async def _check_username_exists_for_other_user(
        self, conn: AsyncConnection, *, username: str, exclude_email: str
    ) -> bool:
        """Check if the username is already taken by another user."""
        query = sa.select(UserRow.uuid).where(
            sa.and_(UserRow.username == username, UserRow.email != exclude_email)
        )
        result = await conn.scalar(query)
        return result is not None

    async def _get_user_by_email(self, session: SASession, email: str) -> UserRow:
        """Private method to get user by email."""
        res = await session.scalar(sa.select(UserRow).where(UserRow.email == email))
        if res is None:
            raise UserNotFound(f"User with email {email} not found.")
        return res

    async def _get_user_by_uuid(self, session: SASession, user_uuid: UUID) -> UserRow:
        """Private method to get user by UUID."""
        res = await session.scalar(sa.select(UserRow).where(UserRow.uuid == user_uuid))
        if res is None:
            raise UserNotFound(f"User with UUID {user_uuid} not found.")
        return res

    async def _get_user_by_email_with_conn(self, conn: AsyncConnection, email: str) -> UserRow:
        """Private method to get user by email using connection."""
        result = await conn.execute(sa.select(users).where(users.c.email == email))
        res = result.first()
        if res is None:
            raise UserNotFound(f"User with email {email} not found.")
        return cast(UserRow, res)

    async def _add_user_to_groups(
        self, db_session: SASession, user_uuid: UUID, domain_name: str, group_ids: list[str]
    ) -> None:
        """Private method to add user to groups including model store project."""
        # Check for model store project
        model_store_query = sa.select(groups.c.id).where(groups.c.type == ProjectType.MODEL_STORE)
        model_store_project = (await db_session.execute(model_store_query)).first()

        gids_to_join = list(group_ids)
        if model_store_project:
            gids_to_join.append(model_store_project.id)

        if gids_to_join:
            query = (
                sa.select(groups.c.id)
                .select_from(groups)
                .where(groups.c.domain_name == domain_name)
                .where(groups.c.id.in_(gids_to_join))
            )
            grps = (await db_session.execute(query)).all()
            if grps:
                group_data = [{"user_id": user_uuid, "group_id": grp.id} for grp in grps]
                group_insert_query = sa.insert(association_groups_users).values(group_data)
                await db_session.execute(group_insert_query)
            else:
                log.warning(
                    "No valid groups found to add user {0} in domain {1}", user_uuid, domain_name
                )
        else:
            log.info("Adding new user {0} with no groups in domain {1}", user_uuid, domain_name)

    async def _validate_and_update_main_access_key(
        self, conn: AsyncConnection, email: str, main_access_key: str
    ) -> None:
        """Private method to validate and update main access key."""
        session = SASession(conn)
        keypair_query = (
            sa.select(KeyPairRow)
            .where(KeyPairRow.access_key == main_access_key)
            .options(
                noload("*"),
                joinedload(KeyPairRow.user_row).options(load_only(UserRow.email)),
            )
        )
        keypair_row = (await session.scalars(keypair_query)).first()
        if not keypair_row:
            raise KeyPairNotFound("Cannot set non-existing access key as the main access key.")
        if keypair_row.user_row.email != email:
            raise KeyPairForbidden("Cannot set another user's access key as the main access key.")

        await conn.execute(
            sa.update(users).where(users.c.email == email).values(main_access_key=main_access_key)
        )

    async def _sync_keypair_roles(
        self, conn: AsyncConnection, user_uuid: UUID, new_role: UserRole
    ) -> None:
        """Private method to sync keypair roles with user role."""
        result = await conn.execute(
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
                await conn.execute(
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
                await conn.execute(
                    sa.update(keypairs)
                    .values({
                        "is_admin": bindparam("is_admin"),
                        "is_active": bindparam("is_active"),
                    })
                    .where(keypairs.c.access_key == bindparam("b_access_key")),
                    kp_updates,
                )

    async def _clear_user_groups(self, conn: AsyncConnection, user_uuid: UUID) -> None:
        """Private method to clear user's group associations."""
        await conn.execute(
            sa.delete(association_groups_users).where(
                association_groups_users.c.user_id == user_uuid
            )
        )

    async def _update_user_groups(
        self, conn: AsyncConnection, user_uuid: UUID, domain_name: str, group_ids: list[str]
    ) -> None:
        """Private method to update user's group associations."""
        # Clear existing groups
        await self._clear_user_groups(conn, user_uuid)

        # Add to new groups
        result = await conn.execute(
            sa.select(groups.c.id)
            .select_from(groups)
            .where(groups.c.domain_name == domain_name)
            .where(groups.c.id.in_(group_ids))
        )
        grps = result.fetchall()
        if grps:
            values = [{"user_id": user_uuid, "group_id": grp.id} for grp in grps]
            await conn.execute(sa.insert(association_groups_users).values(values))

    async def _get_user_uuid_by_email(self, session: SASession, email: str) -> UUID:
        """Get user UUID by email."""
        result = await session.execute(sa.select(UserRow.uuid).where(UserRow.email == email))
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

        endpoint_rows = await EndpointRow.list(
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
            query = sa.select(UserRow)
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
        scope: DomainUserSearchScope,
        querier: BatchQuerier,
    ) -> UserSearchResult:
        """Search users within a domain.

        Args:
            scope: DomainUserSearchScope defining the domain to search within.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            UserSearchResult with matching users and pagination info.
        """
        async with self._db.begin_readonly_session() as db_session:
            query = sa.select(UserRow)
            result = await execute_batch_querier(db_session, query, querier, scope=scope)

            items = [row.UserRow.to_data() for row in result.rows]
            return UserSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    async def search_users_by_project(
        self,
        scope: ProjectUserSearchScope,
        querier: BatchQuerier,
    ) -> UserSearchResult:
        """Search users within a project.

        Joins with association_groups_users to find project members.

        Args:
            scope: ProjectUserSearchScope defining the project to search within.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            UserSearchResult with matching users and pagination info.
        """
        async with self._db.begin_readonly_session() as db_session:
            query = (
                sa.select(UserRow)
                .select_from(UserRow)
                .join(
                    AssocGroupUserRow,
                    UserRow.uuid == AssocGroupUserRow.user_id,
                )
            )
            result = await execute_batch_querier(db_session, query, querier, scope=scope)

            items = [row.UserRow.to_data() for row in result.rows]
            return UserSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )
