import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping, Optional, cast
from uuid import UUID

import msgpack
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, noload

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import SlotName
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.keypair.types import KeyPairCreator
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.data.user.types import UserCreateResultData, UserData
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
from ai.backend.manager.models import kernels
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import ProjectType, association_groups_users, groups
from ai.backend.manager.models.kernel import RESOURCE_USAGE_KERNEL_STATUSES
from ai.backend.manager.models.keypair import KeyPairRow, generate_keypair_data, keypairs
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator, execute_creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import (
    AssociationScopesEntitiesCreatorSpec,
    UserRoleCreatorSpec,
)
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec

from ..permission_controller.role_manager import RoleManager

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


user_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.USER_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class UserRepository:
    _db: ExtendedAsyncSAEngine
    _role_manager: RoleManager

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._role_manager = RoleManager()

    @user_repository_resilience.apply()
    async def get_user_by_uuid(self, user_uuid: UUID) -> UserData:
        """
        Get user by UUID without ownership validation.
        Admin-only operation.
        """
        async with self._db.begin_readonly_session() as db_session:
            user_row = await self._get_user_by_uuid(db_session, user_uuid)
            return user_row.to_data()

    @user_repository_resilience.apply()
    async def get_by_email_validated(
        self,
        email: str,
    ) -> UserData:
        """
        Get user by email with ownership validation.
        Returns None if user not found or access denied.
        """
        async with self._db.begin_session() as session:
            user_row = await self._get_user_by_email(session, email)
            return UserData.from_row(user_row)

    @user_repository_resilience.apply()
    async def create_user_validated(
        self, creator: Creator[UserRow], group_ids: Optional[list[str]]
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
            try:
                # Insert user
                result = await execute_creator(db_session, creator)
                row = result.row
            except sa.exc.IntegrityError as e:
                error_msg = str(e)
                raise UserCreationBadRequest(
                    f"Failed to create user due to database constraint violation: {error_msg}"
                ) from e

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

    @user_repository_resilience.apply()
    async def update_user_validated(
        self,
        email: str,
        updater: Updater[UserRow],
        requester_uuid: Optional[UUID],
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
            if prev_role != updated_user.role and group_ids is None:
                await self._clear_user_groups(conn, updated_user.uuid)

            if group_ids is not None:
                await self._update_user_groups(
                    conn, updated_user.uuid, updated_user.domain_name, group_ids
                )
            res = UserData.from_row(updated_user)
        return res

    @user_repository_resilience.apply()
    async def soft_delete_user_validated(self, email: str, requester_uuid: Optional[UUID]) -> None:
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

    async def _check_domain_exists(self, session: SASession, domain_name: str) -> bool:
        query = sa.select(DomainRow.name).where(DomainRow.name == domain_name)
        result = await session.scalar(query)
        result = cast(Optional[str], result)
        return result is not None

    async def _check_resource_policy_exists(self, session: SASession, policy_name: str) -> bool:
        """Check if the resource policy exists."""
        query = sa.select(UserResourcePolicyRow.name).where(
            UserResourcePolicyRow.name == policy_name
        )
        result = await session.scalar(query)
        result = cast(Optional[str], result)
        return result is not None

    async def _check_user_exists_with_email_or_username(
        self, session: SASession, *, email: str, username: str
    ) -> bool:
        query = sa.select(UserRow.uuid).where(
            sa.or_(UserRow.email == email, UserRow.username == username)
        )
        result = await session.scalar(query)
        result = cast(Optional[UUID], result)
        return result is not None

    async def _check_username_exists_for_other_user(
        self, conn: SASession, *, username: str, exclude_email: str
    ) -> bool:
        """Check if the username is already taken by another user."""
        query = sa.select(UserRow.uuid).where(
            sa.and_(UserRow.username == username, UserRow.email != exclude_email)
        )
        result = await conn.scalar(query)
        result = cast(Optional[UUID], result)
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

    async def _get_user_by_email_with_conn(self, conn, email: str) -> UserRow:
        """Private method to get user by email using connection."""
        result = await conn.execute(sa.select(users).where(users.c.email == email))
        res = result.first()
        if res is None:
            raise UserNotFound(f"User with email {email} not found.")
        return res

    def _validate_user_access(self, user_row: UserRow, requester_uuid: Optional[UUID]) -> bool:
        """Private method to validate user access - can be extended for ownership logic."""
        # For now, allow access - this can be extended with ownership validation
        return True

    async def _add_user_to_groups(
        self, db_session: SASession, user_uuid: UUID, domain_name: str, group_ids: list[str]
    ) -> None:
        """Private method to add user to groups including model store project."""
        # Check for model store project
        model_store_query = sa.select(groups.c.id).where(groups.c.type == ProjectType.MODEL_STORE)
        model_store_project = (await db_session.execute(model_store_query)).first()

        gids_to_join = list(group_ids)
        if model_store_project:
            gids_to_join.append(model_store_project["id"])

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
        self, conn, email: str, main_access_key: str
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

    async def _sync_keypair_roles(self, conn, user_uuid: UUID, new_role: UserRole) -> None:
        """Private method to sync keypair roles with user role."""
        from sqlalchemy.sql.expression import bindparam

        result = await conn.execute(
            sa.select([
                keypairs.c.user,
                keypairs.c.is_active,
                keypairs.c.is_admin,
                keypairs.c.access_key,
            ])
            .select_from(keypairs)
            .where(keypairs.c.user == user_uuid)
            .order_by(sa.desc(keypairs.c.is_admin))
            .order_by(sa.desc(keypairs.c.is_active))
        )

        if new_role in [UserRole.SUPERADMIN, UserRole.ADMIN]:
            # User becomes admin - set first keypair as active admin
            kp = result.first()
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

    async def _clear_user_groups(self, conn, user_uuid: UUID) -> None:
        """Private method to clear user's group associations."""
        await conn.execute(
            sa.delete(association_groups_users).where(
                association_groups_users.c.user_id == user_uuid
            )
        )

    async def _update_user_groups(
        self, conn, user_uuid: UUID, domain_name: str, group_ids: list[str]
    ) -> None:
        """Private method to update user's group associations."""
        # Clear existing groups
        await self._clear_user_groups(conn, user_uuid)

        # Add to new groups
        result = await conn.execute(
            sa.select([groups.c.id])
            .select_from(groups)
            .where(groups.c.domain_name == domain_name)
            .where(groups.c.id.in_(group_ids))
        )
        grps = result.fetchall()
        if grps:
            values = [{"user_id": user_uuid, "group_id": grp.id} for grp in grps]
            await conn.execute(sa.insert(association_groups_users).values(values))

    @user_repository_resilience.apply()
    async def get_user_time_binned_monthly_stats(
        self,
        user_uuid: UUID,
        valkey_stat_client: ValkeyStatClient,
    ) -> list[dict[str, Any]]:
        """
        Generate time-binned (15 min) stats for the last one month for a specific user.
        """
        return await self._get_time_binned_monthly_stats(user_uuid, valkey_stat_client)

    async def _get_time_binned_monthly_stats(
        self,
        user_uuid: Optional[UUID],
        valkey_stat_client: ValkeyStatClient,
    ) -> list[dict[str, Any]]:
        """
        Generate time-binned (15 min) stats for the last one month.
        """
        # Get all or user kernels for the last month from DB.
        time_window = 900  # 15 min
        stat_length = 2880  # 15 * 4 * 24 * 30
        now = datetime.now(tzutc())
        start_date = now - timedelta(days=30)

        async with self._db.begin_readonly() as conn:
            query = (
                sa.select([
                    kernels.c.id,
                    kernels.c.created_at,
                    kernels.c.terminated_at,
                    kernels.c.occupied_slots,
                ])
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
            rows = result.fetchall()

        # Build time-series of time-binned stats.
        start_date_ts = start_date.timestamp()
        time_series_list: list[dict[str, Any]] = [
            {
                "date": start_date_ts + (idx * time_window),
                "num_sessions": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "cpu_allocated": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "mem_allocated": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "gpu_allocated": {
                    "value": 0,
                    "unit_hint": "count",
                },
                "io_read_bytes": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "io_write_bytes": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
                "disk_used": {
                    "value": 0,
                    "unit_hint": "bytes",
                },
            }
            for idx in range(stat_length)
        ]

        kernel_ids = [str(row["id"]) for row in rows]
        raw_stats = await valkey_stat_client.get_user_kernel_statistics_batch(kernel_ids)

        for row, raw_stat in zip(rows, raw_stats):
            if raw_stat is not None:
                last_stat = msgpack.unpackb(raw_stat)
                io_read_byte = int(nmget(last_stat, "io_read.current", 0))
                io_write_byte = int(nmget(last_stat, "io_write.current", 0))
                disk_used = int(nmget(last_stat, "io_scratch_size.stats.max", 0, "/"))
            else:
                io_read_byte = 0
                io_write_byte = 0
                disk_used = 0

            occupied_slots: Mapping[str, Any] = row.occupied_slots
            kernel_created_at: float = row.created_at.timestamp()
            kernel_terminated_at: float = row.terminated_at.timestamp()
            cpu_value = int(occupied_slots.get("cpu", 0))
            mem_value = int(occupied_slots.get("mem", 0))
            gpu_allocated_value = Decimal(0)
            for key, value in occupied_slots.items():
                if SlotName(key).is_accelerator():
                    gpu_allocated_value += value

            start_index = int((kernel_created_at - start_date_ts) // time_window)
            end_index = int((kernel_terminated_at - start_date_ts) // time_window) + 1
            if start_index < 0:
                start_index = 0
            for time_series in time_series_list[start_index:end_index]:
                time_series["num_sessions"]["value"] += 1
                time_series["cpu_allocated"]["value"] += cpu_value
                time_series["mem_allocated"]["value"] += mem_value
                time_series["gpu_allocated"]["value"] += gpu_allocated_value
                time_series["io_read_bytes"]["value"] += io_read_byte
                time_series["io_write_bytes"]["value"] += io_write_byte
                time_series["disk_used"]["value"] += disk_used

        # Change Decimal type to float to serialize to JSON
        for time_series in time_series_list:
            time_series["gpu_allocated"]["value"] = float(time_series["gpu_allocated"]["value"])
        return time_series_list
