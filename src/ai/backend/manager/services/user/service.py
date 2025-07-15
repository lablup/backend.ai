import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserStatus
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.user.admin_repository import AdminUserRepository
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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class MutationResult:
    success: bool
    message: str
    data: Optional[Any]


class UserService:
    _storage_manager: StorageSessionManager
    _valkey_stat_client: ValkeyStatClient
    _agent_registry: AgentRegistry
    _user_repository: UserRepository
    _admin_user_repository: AdminUserRepository

    def __init__(
        self,
        storage_manager: StorageSessionManager,
        valkey_stat_client: ValkeyStatClient,
        agent_registry: AgentRegistry,
        user_repository: UserRepository,
        admin_user_repository: AdminUserRepository,
    ) -> None:
        self._storage_manager = storage_manager
        self._valkey_stat_client = valkey_stat_client
        self._user_repository = user_repository
        self._admin_user_repository = admin_user_repository
        self._agent_registry = agent_registry

    async def create_user(self, action: CreateUserAction) -> CreateUserActionResult:
        # Prepare UserCreator with proper defaults
        user_creator = action.input

        # Set username to email if not provided
        if not user_creator.username:
            user_creator.username = user_creator.email

        # Set status based on is_active if status is not provided
        if user_creator.status is None and user_creator.is_active is not None:
            user_creator.status = (
                UserStatus.ACTIVE if user_creator.is_active else UserStatus.INACTIVE
            )
        elif user_creator.status is None:
            user_creator.status = UserStatus.ACTIVE

        group_ids = user_creator.group_ids if user_creator.group_ids is not None else []

        try:
            user_data_result = await self._user_repository.create_user_validated(
                user_creator, group_ids
            )
            return CreateUserActionResult(
                data=user_data_result,
                success=True,
            )
        except Exception:
            return CreateUserActionResult(
                data=None,
                success=False,
            )

    async def modify_user(self, action: ModifyUserAction) -> ModifyUserActionResult:
        email = action.email
        group_ids = action.group_ids.optional_value()

        # Check if there's anything to update
        if not action.modifier and group_ids is None:
            return ModifyUserActionResult(data=None, success=False)

        try:
            user_data_result = await self._user_repository.update_user_validated(
                email=email,
                user_modifier=action.modifier,
                group_ids=group_ids,
                requester_uuid=None,  # No user context available in ModifyUserAction
            )
            return ModifyUserActionResult(
                success=True,
                data=user_data_result,
            )
        except Exception:
            return ModifyUserActionResult(
                success=False,
                data=None,
            )

    async def delete_user(self, action: DeleteUserAction) -> DeleteUserActionResult:
        try:
            await self._user_repository.soft_delete_user_validated(
                email=action.email,
                requester_uuid=None,  # No user context available in DeleteUserAction
            )
            return DeleteUserActionResult(success=True)
        except Exception:
            return DeleteUserActionResult(success=False)

    async def purge_user(self, action: PurgeUserAction) -> PurgeUserActionResult:
        email = action.email
        log.info("Purging all records of the user {0}...", email)

        # Check if user exists
        user_data = await self._admin_user_repository.get_by_email_force(email)
        if not user_data:
            raise RuntimeError(f"User not found (email: {email})")

        user_uuid = user_data.uuid

        # Check for active vfolder mounts
        if await self._admin_user_repository.check_user_vfolder_mounted_to_active_kernels_force(
            user_uuid
        ):
            raise RuntimeError(
                "Some of user's virtual folders are mounted to active kernels. "
                "Terminate those kernels first.",
            )

        # Handle shared vfolders migration
        if action.purge_shared_vfolders.optional_value():
            await self._admin_user_repository.migrate_shared_vfolders_force(
                deleted_user_uuid=user_uuid,
                target_user_uuid=action.user_info_ctx.uuid,
                target_user_email=action.user_info_ctx.email,
            )

        # Handle endpoint ownership delegation
        if action.delegate_endpoint_ownership.optional_value():
            await self._admin_user_repository.delegate_endpoint_ownership_force(
                user_uuid=user_uuid,
                target_user_uuid=action.user_info_ctx.uuid,
                target_main_access_key=action.user_info_ctx.main_access_key,
            )
            await self._admin_user_repository.delete_endpoints_force(
                user_uuid=user_uuid,
                delete_destroyed_only=True,
            )
        else:
            await self._admin_user_repository.delete_endpoints_force(
                user_uuid=user_uuid,
                delete_destroyed_only=False,
            )

        # Handle active sessions
        if active_sessions := await self._admin_user_repository.retrieve_active_sessions_force(
            user_uuid
        ):
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

        # Delete vfolders
        await self._admin_user_repository.delete_user_vfolders_force(
            user_uuid=user_uuid,
            storage_manager=self._storage_manager,
        )

        # Finally purge the user completely
        await self._admin_user_repository.purge_user_force(email)

        return PurgeUserActionResult(success=True)

    async def user_month_stats(self, action: UserMonthStatsAction) -> UserMonthStatsActionResult:
        from datetime import datetime, timedelta
        from uuid import UUID

        from dateutil.tz import tzutc

        # Get raw kernel data from repository
        user_uuid = UUID(action.user_id)
        start_date = datetime.now(tzutc()) - timedelta(days=30)

        kernels = await self._user_repository.get_user_kernels_for_stats(
            user_uuid=user_uuid,
            start_date=start_date,
        )

        # Process statistics using ValkeyStatClient
        stats = await self._process_user_time_binned_monthly_stats(kernels)
        return UserMonthStatsActionResult(stats=[stats])

    async def _process_user_time_binned_monthly_stats(self, kernels: list[dict]) -> dict[str, Any]:
        """
        Process user time-binned monthly statistics.
        This method recreates the statistics processing logic that was moved from repository.
        """
        from datetime import datetime, timedelta
        from decimal import Decimal

        import msgpack
        from dateutil.tz import tzutc

        from ai.backend.common.types import ResourceSlot

        # Constants
        TIME_WINDOW = 900  # 15 minutes in seconds
        DATA_LENGTH = 2880  # 15 min × 4 × 24 × 30 days
        now = datetime.now(tzutc())

        # Initialize statistics structure
        stats = {
            "num_sessions": [0] * DATA_LENGTH,
            "cpu_allocated": [0] * DATA_LENGTH,
            "mem_allocated": [0] * DATA_LENGTH,
            "gpu_allocated": [0] * DATA_LENGTH,
            "io_read_bytes": [0] * DATA_LENGTH,
            "io_write_bytes": [0] * DATA_LENGTH,
            "disk_used": [0] * DATA_LENGTH,
        }

        if not kernels:
            return stats

        # Get kernel IDs for statistics fetching
        kernel_ids = [kernel["id"] for kernel in kernels]

        # Fetch raw statistics from ValkeyStatClient
        raw_stats = await self._valkey_stat_client.get_user_kernel_statistics_batch(kernel_ids)

        # Process each kernel
        for idx, kernel in enumerate(kernels):
            created_at = kernel["created_at"]
            terminated_at = kernel["terminated_at"]
            occupied_slots = ResourceSlot.from_json(kernel["occupied_slots"])

            # Calculate time range for this kernel
            start_time = max(created_at, now - timedelta(days=30))
            end_time = terminated_at if terminated_at else now

            # Calculate time bin indices
            start_bin = max(
                0, int((start_time - (now - timedelta(days=30))).total_seconds() // TIME_WINDOW)
            )
            end_bin = min(
                DATA_LENGTH - 1,
                int((end_time - (now - timedelta(days=30))).total_seconds() // TIME_WINDOW),
            )

            # Process raw statistics for this kernel
            kernel_stats = raw_stats[idx] if idx < len(raw_stats) else None

            # Add resource allocations to time bins
            for bin_idx in range(start_bin, end_bin + 1):
                stats["num_sessions"][bin_idx] += 1
                stats["cpu_allocated"][bin_idx] += int(occupied_slots.get("cpu", 0))
                stats["mem_allocated"][bin_idx] += int(occupied_slots.get("mem", 0))

                # Handle GPU allocation (both CUDA devices and shares)
                gpu_count = 0
                gpu_count += len(occupied_slots.get("cuda.devices", []))
                gpu_count += int(occupied_slots.get("cuda.shares", 0))
                stats["gpu_allocated"][bin_idx] += gpu_count

                # Process I/O and disk statistics if available
                if kernel_stats:
                    try:
                        # Unpack msgpack-encoded statistics
                        unpacked_stats = msgpack.unpackb(kernel_stats, raw=False)

                        # Extract I/O statistics
                        io_read = unpacked_stats.get(f"io_read_bytes_{bin_idx}", 0)
                        io_write = unpacked_stats.get(f"io_write_bytes_{bin_idx}", 0)
                        disk_used = unpacked_stats.get(f"disk_used_{bin_idx}", 0)

                        stats["io_read_bytes"][bin_idx] += int(io_read)
                        stats["io_write_bytes"][bin_idx] += int(io_write)
                        stats["disk_used"][bin_idx] += int(disk_used)
                    except Exception:
                        # Continue if statistics unpacking fails
                        pass

        # Convert any Decimal types to float for JSON serialization
        for key in stats:
            stats[key] = [float(x) if isinstance(x, Decimal) else x for x in stats[key]]

        return stats

    async def admin_month_stats(self, action: AdminMonthStatsAction) -> AdminMonthStatsActionResult:
        stats = await self._admin_user_repository.get_admin_time_binned_monthly_stats_force(
            valkey_stat_client=self._valkey_stat_client,
        )
        return AdminMonthStatsActionResult(stats=stats)
