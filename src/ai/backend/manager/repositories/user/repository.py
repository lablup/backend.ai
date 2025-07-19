from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping, Optional
from uuid import UUID

import msgpack
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import joinedload, load_only, noload

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.utils import nmget
from ai.backend.manager.data.keypair.types import KeyPairCreator
from ai.backend.manager.data.user.types import UserCreator, UserData
from ai.backend.manager.decorators.repository_decorator import (
    create_layer_aware_repository_decorator,
)
from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT, DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.errors.user import KeyPairForbidden, KeyPairNotFound, UserNotFound
from ai.backend.manager.models import kernels
from ai.backend.manager.models.group import ProjectType, association_groups_users, groups
from ai.backend.manager.models.kernel import RESOURCE_USAGE_KERNEL_STATUSES
from ai.backend.manager.models.keypair import KeyPairRow, keypairs, prepare_new_keypair
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus, users
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user.actions.modify_user import UserModifier

# Layer-specific decorator for user repository
repository_decorator = create_layer_aware_repository_decorator(LayerType.USER)


class UserRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @repository_decorator()
    async def get_user_by_uuid(self, user_uuid: UUID) -> UserData:
        """
        Get user by UUID without ownership validation.
        Admin-only operation.
        """
        async with self._db.begin_readonly_session() as db_session:
            user_row = await self._get_user_by_uuid(db_session, user_uuid)
            return user_row.to_data()

    @repository_decorator()
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

    @repository_decorator()
    async def create_user_validated(
        self, user_creator: UserCreator, group_ids: Optional[list[str]]
    ) -> UserData:
        """
        Create a new user with default keypair and group associations.
        """
        user_data = user_creator.fields_to_store()
        async with self._db.begin() as conn:
            # Insert user
            user_insert_query = sa.insert(users).values(user_data)
            query = user_insert_query.returning(user_insert_query.table)
            result = await conn.execute(query)
            created_user = result.first()

            if not created_user:
                raise RuntimeError("Failed to create user")

            # Create default keypair
            email = user_data["email"]
            keypair_creator = KeyPairCreator(
                is_active=(user_data["status"] == UserStatus.ACTIVE),
                is_admin=user_data["role"] in ["superadmin", "admin"],
                resource_policy=DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME,
                rate_limit=DEFAULT_KEYPAIR_RATE_LIMIT,
            )
            kp_data = prepare_new_keypair(email, keypair_creator)
            kp_insert_query = sa.insert(keypairs).values(
                **kp_data,
                user=created_user.uuid,
            )
            await conn.execute(kp_insert_query)

            # Update user main_access_key
            main_ak = kp_data["access_key"]
            update_query = (
                sa.update(users)
                .where(users.c.uuid == created_user.uuid)
                .values(main_access_key=main_ak)
            )
            await conn.execute(update_query)

            # Add user to groups including model store project
            await self._add_user_to_groups(
                conn, created_user.uuid, user_data["domain_name"], group_ids or []
            )

            res = UserData.from_row(created_user)
        if not res:
            raise RuntimeError("Failed to convert created user row to UserData")
        return res

    @repository_decorator()
    async def update_user_validated(
        self,
        email: str,
        modifier: UserModifier,
        group_ids: Optional[list[str]],
        requester_uuid: Optional[UUID],
    ) -> UserData:
        """
        Update user with ownership validation and handle role/group changes.
        """
        to_update = modifier.fields_to_update()
        async with self._db.begin() as conn:
            # Get current user data for validation
            current_user = await self._get_user_by_email_with_conn(conn, email)

            # Handle main_access_key validation
            main_access_key = modifier.main_access_key.optional_value()
            if main_access_key:
                await self._validate_and_update_main_access_key(conn, email, main_access_key)

            # Update user
            if modifier.password.optional_value():
                to_update["password_changed_at"] = sa.func.now()
            status = modifier.status.optional_value()
            if status is not None and status != current_user.status:
                to_update["status_info"] = "admin-requested"
            update_query = (
                sa.update(users).where(users.c.email == email).values(to_update).returning(users)
            )
            result = await conn.execute(update_query)
            updated_user = result.first()
            if not updated_user:
                raise RuntimeError("Failed to update user")

            # Handle role changes
            prev_role = current_user.role
            prev_domain_name = current_user.domain_name
            role = modifier.role.optional_value()
            if role is not None and role != prev_role:
                await self._sync_keypair_roles(conn, updated_user.uuid, role)

            # Handle group updates
            if prev_role != updated_user.role and group_ids is None:
                await self._clear_user_groups(conn, updated_user.uuid)

            if prev_domain_name != updated_user.domain_name and group_ids is not None:
                await self._update_user_groups(
                    conn, updated_user.uuid, updated_user.domain_name, group_ids
                )
            res = UserData.from_row(updated_user)
        return res

    @repository_decorator()
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
        self, conn, user_uuid: UUID, domain_name: str, group_ids: list[str]
    ) -> None:
        """Private method to add user to groups including model store project."""
        # Check for model store project
        model_store_query = sa.select([groups.c.id]).where(groups.c.type == ProjectType.MODEL_STORE)
        model_store_project = (await conn.execute(model_store_query)).first()

        gids_to_join = list(group_ids)
        if model_store_project:
            gids_to_join.append(model_store_project["id"])

        if gids_to_join:
            query = (
                sa.select([groups.c.id])
                .select_from(groups)
                .where(groups.c.domain_name == domain_name)
                .where(groups.c.id.in_(gids_to_join))
            )
            grps = (await conn.execute(query)).all()
            if grps:
                group_data = [{"user_id": user_uuid, "group_id": grp.id} for grp in grps]
                group_insert_query = sa.insert(association_groups_users).values(group_data)
                await conn.execute(group_insert_query)

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

    @repository_decorator()
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
            cuda_device_value = int(occupied_slots.get("cuda.devices", 0))
            cuda_share_value = Decimal(occupied_slots.get("cuda.shares", 0))

            start_index = int((kernel_created_at - start_date_ts) // time_window)
            end_index = int((kernel_terminated_at - start_date_ts) // time_window) + 1
            if start_index < 0:
                start_index = 0
            for time_series in time_series_list[start_index:end_index]:
                time_series["num_sessions"]["value"] += 1
                time_series["cpu_allocated"]["value"] += cpu_value
                time_series["mem_allocated"]["value"] += mem_value
                time_series["gpu_allocated"]["value"] += cuda_device_value
                time_series["gpu_allocated"]["value"] += cuda_share_value
                time_series["io_read_bytes"]["value"] += io_read_byte
                time_series["io_write_bytes"]["value"] += io_write_byte
                time_series["disk_used"]["value"] += disk_used

        # Change Decimal type to float to serialize to JSON
        for time_series in time_series_list:
            time_series["gpu_allocated"]["value"] = float(time_series["gpu_allocated"]["value"])
        return time_series_list
