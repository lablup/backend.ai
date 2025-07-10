import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Awaitable, Callable, Mapping, Optional
from uuid import UUID

import msgpack
from dateutil.tz import tzutc

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserStatus
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    execute_with_txn_retry,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.user.actions.admin_month_stats import (
    AdminMonthStatsAction,
    AdminMonthStatsActionResult,
)
from ai.backend.manager.services.user.actions.create_user import (
    CreateUserAction,
    CreateUserActionResult,
)
from ai.backend.manager.services.user.actions.delete_user import (
    DeleteUserAction,
    DeleteUserActionResult,
)
from ai.backend.manager.services.user.actions.modify_user import (
    ModifyUserAction,
    ModifyUserActionResult,
)
from ai.backend.manager.services.user.actions.purge_user import (
    PurgeUserAction,
    PurgeUserActionResult,
)
from ai.backend.manager.services.user.actions.user_month_stats import (
    UserMonthStatsAction,
    UserMonthStatsActionResult,
)
from ai.backend.manager.services.user.type import UserData
from ai.backend.manager.errors.exceptions import UserNotFound

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


class UserService:
    _user_repository: UserRepository
    _agent_registry: AgentRegistry

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
        redis_stat: RedisConnectionInfo,
        agent_registry: AgentRegistry,
    ) -> None:
        self._user_repository = UserRepository(
            db=db,
            storage_manager=storage_manager,
            redis_stat=redis_stat,
            agent_registry=agent_registry,
        )
        self._agent_registry = agent_registry

    async def create_user(self, action: CreateUserAction) -> CreateUserActionResult:
        username = action.input.username if action.input.username else action.input.email
        _status = UserStatus.ACTIVE  # TODO: Need to be set in action explicitly not in service (integrate is_active and status)
        if action.input.status is None and action.input.is_active is not None:
            _status = UserStatus.ACTIVE if action.input.is_active else UserStatus.INACTIVE
        if action.input.status is not None:
            _status = action.input.status
        group_ids = [] if action.input.group_ids is None else [UUID(gid) for gid in action.input.group_ids]

        user_data = {
            "username": username,
            "email": action.input.email,
            "password": action.input.password,
            "need_password_change": action.input.need_password_change,
            "full_name": action.input.full_name,
            "description": action.input.description,
            "status": _status,
            "status_info": "admin-requested",  # user mutation is only for admin
            "domain_name": action.input.domain_name,
            "role": action.input.role,
            "allowed_client_ip": action.input.allowed_client_ip,
            "totp_activated": action.input.totp_activated,
            "resource_policy": action.input.resource_policy,
            "sudo_session_enabled": action.input.sudo_session_enabled,
        }
        if action.input.container_uid is not None:
            user_data["container_uid"] = action.input.container_uid
        if action.input.container_main_gid is not None:
            user_data["container_main_gid"] = action.input.container_main_gid
        if action.input.container_gids is not None:
            user_data["container_gids"] = action.input.container_gids

        async def _do_mutate() -> MutationResult:
            created_user = await self._user_repository.create_user(user_data, group_ids)
            return MutationResult(
                success=True if created_user is not None else False,
                message="User created successfully",
                data=created_user,
            )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)
        return CreateUserActionResult(
            data=UserData.from_row(result.data),
            success=result.success,
        )

    async def modify_user(self, action: ModifyUserAction) -> ModifyUserActionResult:
        email = action.email
        data = action.modifier.fields_to_update()
        if data.get("password") is None:
            data.pop("password", None)

        group_ids = action.group_ids.optional_value()

        if not data and group_ids is None:
            return ModifyUserActionResult(data=None, success=False)
        if data.get("status") is None and data.get("is_active") is not None:
            data["status"] = UserStatus.ACTIVE if data["is_active"] else UserStatus.INACTIVE

        if data.get("password") is not None:
            import sqlalchemy as sa

            data["password_changed_at"] = sa.func.now()

        main_access_key: str | None = data.get("main_access_key")

        async def _do_mutate() -> MutationResult:
            try:
                (
                    prev_domain_name,
                    prev_role,
                    prev_status,
                ) = await self._user_repository.get_user_domain_and_role(email)
            except Exception:
                raise UserNotFound(f"User with email {email} not found")

            user_update_data = data.copy()
            if "status" in data and prev_status != data["status"]:
                user_update_data["status_info"] = "admin-requested"

            if main_access_key is not None:
                await self._user_repository.validate_main_access_key(email, main_access_key)
                await self._user_repository.update_user_main_access_key(email, main_access_key)

            updated_user = await self._user_repository.update_user(email, user_update_data)
            if updated_user is None:
                raise UserNotFound(f"User with email {email} not found")

            if "role" in data and data["role"] != prev_role:
                await self._user_repository.update_user_keypairs_role(
                    updated_user.uuid, data["role"]
                )

            if prev_domain_name != updated_user.domain_name and not group_ids:
                await self._user_repository.clear_user_groups(updated_user.uuid)

            if group_ids:
                group_uuids = [UUID(gid) for gid in group_ids]
                await self._user_repository.update_user_groups(
                    updated_user.uuid, updated_user.domain_name, group_uuids
                )

            return MutationResult(
                success=True,
                message="User modified successfully",
                data=updated_user,
            )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)

        return ModifyUserActionResult(
            success=result.success,
            data=UserData.from_row(result.data),
        )

    async def delete_user(self, action: DeleteUserAction) -> DeleteUserActionResult:
        async def _do_mutate() -> MutationResult:
            await self._user_repository.deactivate_user_keypairs(action.email)
            await self._user_repository.delete_user(action.email)

            return MutationResult(
                success=True,
                message="User deleted successfully",
                data=None,
            )

        result: MutationResult = await self._db_mutation_wrapper(_do_mutate)
        return DeleteUserActionResult(
            success=result.success,
        )

    async def purge_user(self, action: PurgeUserAction) -> PurgeUserActionResult:
        email = action.email

        async def _delete(conn) -> None:
            user_uuid = await self._user_repository.get_user_uuid_by_email(email)
            log.info("Purging all records of the user {0}...", email)
            if user_uuid is None:
                raise RuntimeError(f"User not found (email: {email})")

            if await self._user_repository.user_vfolder_mounted_to_active_kernels(user_uuid):
                raise RuntimeError(
                    "Some of user's virtual folders are mounted to active kernels. "
                    "Terminate those kernels first.",
                )

            if action.purge_shared_vfolders.optional_value():
                await self._user_repository.migrate_shared_vfolders(
                    deleted_user_uuid=user_uuid,
                    target_user_uuid=action.user_info_ctx.uuid,
                    target_user_email=action.user_info_ctx.email,
                )

            if action.delegate_endpoint_ownership.optional_value():
                async with self._user_repository._db.begin_session() as db_session:
                    await EndpointRow.delegate_endpoint_ownership(
                        db_session,
                        user_uuid,
                        action.user_info_ctx.uuid,
                        action.user_info_ctx.main_access_key,
                    )
                await self._user_repository.delete_endpoint(user_uuid, delete_destroyed_only=True)
            else:
                await self._user_repository.delete_endpoint(user_uuid, delete_destroyed_only=False)

            if active_sessions := await self._user_repository.retrieve_active_sessions(user_uuid):
                tasks = [
                    asyncio.create_task(
                        self._agent_registry.destroy_session(
                            session,
                            forced=True,
                            reason=KernelLifecycleEventReason.USER_PURGED,
                        )
                    )
                    for session in active_sessions
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for sess, result in zip(active_sessions, results):
                    if isinstance(result, Exception):
                        log.warning(f"Session {sess.id} not terminated properly: {result}")

            await self._user_repository.delete_vfolders(user_uuid)
            await self._user_repository.delete_error_logs(user_uuid)
            await self._user_repository.delete_keypairs(user_uuid)
            await self._user_repository.delete_user_from_db(email)

        async with self._user_repository._db.connect() as db_conn:
            await execute_with_txn_retry(_delete, self._user_repository._db.begin_session, db_conn)

        return PurgeUserActionResult(success=True)

    async def _db_mutation_wrapper(
        self, _do_mutate: Callable[[], Awaitable[MutationResult]]
    ) -> MutationResult:
        try:
            return await execute_with_retry(_do_mutate)
        except Exception as e:
            import sqlalchemy as sa

            if isinstance(e, sa.exc.IntegrityError):
                log.warning("db_mutation_wrapper(): integrity error ({})", repr(e))
                return MutationResult(success=False, message=f"integrity error: {e}", data=None)
            elif isinstance(e, sa.exc.StatementError):
                log.warning(
                    "db_mutation_wrapper(): statement error ({})\n{}",
                    repr(e),
                    e.statement or "(unknown)",
                )
                orig_exc = e.orig
                return MutationResult(success=False, message=str(orig_exc), data=None)
            elif isinstance(e, (asyncio.CancelledError, asyncio.TimeoutError)):
                raise
            else:
                log.exception("db_mutation_wrapper(): other error")
                raise

    async def user_month_stats(self, action: UserMonthStatsAction) -> UserMonthStatsActionResult:
        stats = await self._get_time_binned_monthly_stats(user_uuid=action.user_id)
        return UserMonthStatsActionResult(stats=stats)

    async def admin_month_stats(self, action: AdminMonthStatsAction) -> AdminMonthStatsActionResult:
        stats = await self._get_time_binned_monthly_stats(user_uuid=None)
        return AdminMonthStatsActionResult(stats=stats)

    async def _get_time_binned_monthly_stats(self, user_uuid=None):
        time_window = 900
        stat_length = 2880
        now = datetime.now(tzutc())
        start_date = now - timedelta(days=30)

        rows = await self._user_repository.get_kernels_for_monthly_stats(user_uuid)

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
        raw_stats = await self._user_repository.get_kernel_stats_from_redis(kernel_ids)

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

        for time_series in time_series_list:
            time_series["gpu_allocated"]["value"] = float(time_series["gpu_allocated"]["value"])
        return time_series_list
