from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import msgpack
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import AccessKey, SlotName
from ai.backend.common.utils import nmget
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import GeneratedKeyPairData, KeyPairCreator, KeyPairData
from ai.backend.manager.data.user.types import (
    BulkUserCreateResultData,
    BulkUserUpdateResultData,
    UserCreateResultData,
    UserData,
    UserSearchResult,
)
from ai.backend.manager.errors.user import KeyPairNotFound
from ai.backend.manager.models.keypair.creators import KeypairCreator
from ai.backend.manager.models.keypair.purgers import NonDefaultKeypairPurger
from ai.backend.manager.models.keypair.queriers import DefaultKeypairQuerier
from ai.backend.manager.models.keypair.row import generate_keypair_data
from ai.backend.manager.models.keypair.scopes import UserKeypairOperationScope
from ai.backend.manager.models.keypair.updaters import KeypairUpdater
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.user.scopes import (
    DomainUserOperationScope,
    ProjectUserOperationScope,
    RoleUserOperationScope,
)
from ai.backend.manager.models.user.updaters import UserUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.querier import BatchQuerier
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.user.creators import UserCreateSpec
from ai.backend.manager.repositories.user.db_source import UserDBSource

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
    _db_source: UserDBSource

    def __init__(self, db: ExtendedAsyncSAEngine, v2_ops_provider: V2DBOpsProvider) -> None:
        self._db_source = UserDBSource(db)
        self._v2_ops = v2_ops_provider

    @user_repository_resilience.apply()
    async def default_access_key(self, user_id: UserID) -> AccessKey | None:
        """The key a user authorizes with, or ``None`` if they marked no active one."""
        async with self._v2_ops.read_ops() as r:
            designated = await r.query_owned_fields(DefaultKeypairQuerier(), [user_id])
        keypair = designated.get(user_id)
        return AccessKey(keypair.access_key) if keypair is not None else None

    @user_repository_resilience.apply()
    async def get_user_by_uuid(self, user_uuid: UUID) -> UserData:
        """
        Get user by UUID without ownership validation.
        Admin-only operation.
        """
        return await self._db_source.get_user_by_uuid(user_uuid)

    @user_repository_resilience.apply()
    async def get_by_email_validated(
        self,
        email: str,
    ) -> UserData:
        """
        Get user by email with ownership validation.
        Returns None if user not found or access denied.
        """
        return await self._db_source.get_by_email_validated(email)

    @user_repository_resilience.apply()
    async def create_user_validated(
        self, creator: UserCreator, group_ids: list[str] | None
    ) -> UserCreateResultData:
        """
        Create a new user with default keypair and group associations.
        """
        return await self._db_source.create_user_validated(creator, group_ids)

    @user_repository_resilience.apply()
    async def bulk_create_users_validated(
        self,
        items: list[UserCreateSpec],
    ) -> BulkUserCreateResultData:
        """
        Create multiple users with partial failure support.
        """
        return await self._db_source.bulk_create_users_validated(items)

    @user_repository_resilience.apply()
    async def bulk_update_users_validated(
        self,
        items: list[UserUpdater],
    ) -> BulkUserUpdateResultData:
        """
        Update multiple users with partial failure support.
        """
        return await self._db_source.bulk_update_users_validated(items)

    @user_repository_resilience.apply()
    async def update_user_by_uuid_validated(self, updater: UserUpdater) -> UserData:
        """Update user by UUID with validation and handle role/group changes."""
        return await self._db_source.update_user_by_uuid_validated(updater)

    @user_repository_resilience.apply()
    async def delete_user_by_uuid_validated(self, user_uuid: UUID) -> None:
        """Soft delete user by UUID, setting status to DELETED and deactivating keypairs."""
        await self._db_source.delete_user_by_uuid_validated(user_uuid)

    @user_repository_resilience.apply()
    async def purge_user_by_uuid(self, user_uuid: UUID) -> None:
        """Completely purge user and all associated data by UUID."""
        await self._db_source.purge_user_by_uuid(user_uuid)

    @user_repository_resilience.apply()
    async def check_user_vfolder_mounted_to_active_kernels(self, user_uuid: UUID) -> bool:
        """Check if user's vfolders are mounted to active kernels."""
        return await self._db_source.check_user_vfolder_mounted_to_active_kernels(user_uuid)

    @user_repository_resilience.apply()
    async def migrate_shared_vfolders(
        self,
        deleted_user_uuid: UUID,
        target_user_uuid: UUID,
        target_user_email: str,
    ) -> int:
        """Migrate shared virtual folders ownership to target user."""
        return await self._db_source.migrate_shared_vfolders(
            deleted_user_uuid, target_user_uuid, target_user_email
        )

    @user_repository_resilience.apply()
    async def retrieve_active_sessions(self, user_uuid: UUID) -> list[SessionRow]:
        """Retrieve active sessions for a user."""
        return await self._db_source.retrieve_active_sessions(user_uuid)

    @user_repository_resilience.apply()
    async def delegate_endpoint_ownership(
        self,
        user_uuid: UUID,
        target_user_uuid: UUID,
    ) -> None:
        """Delegate endpoint ownership to another user."""
        await self._db_source.delegate_endpoint_ownership(user_uuid, target_user_uuid)

    @user_repository_resilience.apply()
    async def delete_endpoints(
        self,
        user_uuid: UUID,
        delete_destroyed_only: bool = False,
    ) -> None:
        """Delete user's endpoints."""
        await self._db_source.delete_endpoints(user_uuid, delete_destroyed_only)

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

    @user_repository_resilience.apply()
    async def get_admin_time_binned_monthly_stats(
        self,
        valkey_stat_client: ValkeyStatClient,
    ) -> list[dict[str, Any]]:
        """Get time-binned monthly statistics for all users."""
        return await self._get_time_binned_monthly_stats(None, valkey_stat_client)

    @user_repository_resilience.apply()
    async def delete_user_vfolders(
        self,
        user_uuid: UUID,
        storage_manager: StorageSessionManager,
    ) -> int:
        """Delete user's all virtual folders and their physical data."""
        return await self._db_source.delete_vfolders(user_uuid, storage_manager)

    @user_repository_resilience.apply()
    async def delete_user_keypairs_with_valkey(
        self,
        user_uuid: UUID,
        valkey_stat_client: ValkeyStatClient,
    ) -> int:
        """Delete user's keypairs including Valkey concurrency cleanup."""
        return await self._db_source.delete_keypairs_with_valkey(user_uuid, valkey_stat_client)

    @user_repository_resilience.apply()
    async def search_users(self, querier: BatchQuerier) -> UserSearchResult:
        """Search all users with pagination and filters (admin only).

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            UserSearchResult with matching users and pagination info.
        """
        return await self._db_source.search_users(querier=querier)

    @user_repository_resilience.apply()
    async def search_users_by_domain(
        self, scope: DomainUserOperationScope, querier: BatchQuerier
    ) -> UserSearchResult:
        """Search users within a domain.

        Args:
            scope: DomainUserOperationScope defining the domain to search within.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            UserSearchResult with matching users and pagination info.
        """
        return await self._db_source.search_users_by_domain(scope, querier)

    @user_repository_resilience.apply()
    async def search_users_by_project(
        self, scope: ProjectUserOperationScope, querier: BatchQuerier
    ) -> UserSearchResult:
        """Search users within a project.

        Args:
            scope: ProjectUserOperationScope defining the project to search within.
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            UserSearchResult with matching users and pagination info.
        """
        return await self._db_source.search_users_by_project(scope, querier)

    @user_repository_resilience.apply()
    async def search_users_by_role(
        self, scope: RoleUserOperationScope, querier: BatchQuerier
    ) -> UserSearchResult:
        """Search users assigned to a role."""
        return await self._db_source.search_users_by_role(scope, querier)

    @user_repository_resilience.apply()
    async def issue_my_keypair(self, user_id: UserID) -> GeneratedKeyPairData:
        """Issue a new keypair for a user, following the one they authorize with."""
        creator = await self._db_source.keypair_settings_to_inherit(user_id)
        return await self._create_keypair(user_id, creator)

    @user_repository_resilience.apply()
    async def admin_create_keypair(
        self, user_id: UserID, creator: KeyPairCreator
    ) -> GeneratedKeyPairData:
        """Issue a keypair for a named user."""
        return await self._create_keypair(user_id, creator)

    async def _create_keypair(
        self, user_id: UserID, creator: KeyPairCreator
    ) -> GeneratedKeyPairData:
        async with self._v2_ops.write_ops() as w:
            keypair = await w.create_field(
                user_id,
                KeypairCreator(
                    secrets=generate_keypair_data(),
                    is_active=creator.is_active,
                    is_admin=creator.is_admin,
                    resource_policy=creator.resource_policy,
                    rate_limit=creator.rate_limit,
                ),
            )
        return GeneratedKeyPairData(keypair=keypair)

    @user_repository_resilience.apply()
    async def keypair(self, keypair_id: KeyPairID) -> KeyPairData:
        """Read one keypair by its id."""
        return await self._db_source.keypair(keypair_id)

    @user_repository_resilience.apply()
    async def purge_keypair(self, keypair_id: KeyPairID) -> KeyPairData | None:
        """Remove one keypair unless it is the key its user authorizes with.

        ``None`` when nothing was removed — the row is gone, or the guard refused.
        """
        async with self._v2_ops.write_ops() as w:
            return await w.purge_guarded_field_entity(
                NonDefaultKeypairPurger(keypair_id=keypair_id)
            )

    @user_repository_resilience.apply()
    async def update_keypair(self, updater: KeypairUpdater) -> KeyPairData | None:
        """Write one keypair's settings unless the write would deactivate the key its
        user authorizes with.

        ``None`` when nothing was written — the row is gone, or the guard refused.
        """
        async with self._v2_ops.write_ops() as w:
            return await w.update_guarded_data(updater)

    @user_repository_resilience.apply()
    async def switch_default_access_key(self, user_id: UserID, access_key: AccessKey) -> None:
        """Move the ``is_default`` marker among the user's keypairs onto ``access_key``."""
        await self._db_source.switch_default_access_key(user_id, access_key)

    @user_repository_resilience.apply()
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
        return await self._db_source.search_my_keypairs(scope, querier)

    @user_repository_resilience.apply()
    async def admin_search_keypairs(
        self,
        querier: BatchQuerier,
    ) -> SearchResult[KeyPairData]:
        """Admin search all keypairs without scope restriction."""
        return await self._db_source.admin_search_keypairs(querier)

    @user_repository_resilience.apply()
    async def update_keypair_column(self, updater: DataUpdater[Any, KeyPairData]) -> KeyPairData:
        """Write one column of a keypair row."""
        async with self._v2_ops.write_ops() as w:
            data = await w.update_data(updater)
            if data is None:
                raise KeyPairNotFound(f"Keypair not found: {updater.target_id_value()}")
            return data

    @user_repository_resilience.apply()
    async def admin_get_keypair(self, access_key: str) -> KeyPairData:
        """Admin retrieves a single keypair by access key."""
        return await self._db_source.admin_get_keypair(access_key)

    @user_repository_resilience.apply()
    async def admin_update_ssh_keypair(
        self,
        access_key: str,
        ssh_public_key: str,
        ssh_private_key: str,
    ) -> None:
        """Admin registers (overwrites) a user's SSH keypair."""
        await self._db_source.admin_update_ssh_keypair(
            access_key=access_key,
            ssh_public_key=ssh_public_key,
            ssh_private_key=ssh_private_key,
        )

    @user_repository_resilience.apply()
    async def admin_clear_ssh_keypair(self, access_key: str) -> None:
        """Admin clears a user's SSH keypair."""
        await self._db_source.admin_clear_ssh_keypair(access_key=access_key)

    @user_repository_resilience.apply()
    async def admin_get_ssh_public_key(self, access_key: str) -> str | None:
        """Admin retrieves a user's SSH public key (never the private key)."""
        return await self._db_source.admin_get_ssh_public_key(access_key=access_key)

    async def _get_time_binned_monthly_stats(
        self,
        user_uuid: UUID | None,
        valkey_stat_client: ValkeyStatClient,
    ) -> list[dict[str, Any]]:
        """
        Generate time-binned (15 min) stats for the last one month.
        """
        time_window = 900  # 15 min
        stat_length = 2880  # 15 * 4 * 24 * 30
        now = datetime.now(tzutc())
        start_date = now - timedelta(days=30)

        # DB query via db_source
        rows = await self._db_source.get_kernel_rows_for_monthly_stats(user_uuid)

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

        # Valkey batch fetch
        kernel_ids = [str(row.id) for row in rows]
        raw_stats = await valkey_stat_client.get_user_kernel_statistics_batch(kernel_ids)

        for row, raw_stat in zip(rows, raw_stats, strict=True):
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
