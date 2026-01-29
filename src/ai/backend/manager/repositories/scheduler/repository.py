"""Repository pattern implementation for schedule operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    SessionId,
    SlotName,
    SlotTypes,
    VFolderMount,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelListResult, KernelStatus
from ai.backend.manager.data.session.types import SessionInfo, SessionStatus
from ai.backend.manager.exceptions import ErrorStatusInfo
from ai.backend.manager.models.scheduling_history.row import SessionSchedulingHistoryRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.sokovan.data import (
    AllocationBatch,
    KernelCreationInfo,
    SessionRunningData,
    SessionsForPullWithImages,
    SessionsForStartWithImages,
    SessionWithKernels,
)
from ai.backend.manager.types import UserScope

from .cache_source.cache_source import ScheduleCacheSource
from .db_source.db_source import ScheduleDBSource
from .types.base import SchedulingSpec
from .types.results import ScheduledSessionData
from .types.scheduling import SchedulingData
from .types.search import (
    SessionWithKernelsAndUserSearchResult,
    SessionWithKernelsSearchResult,
)
from .types.session import (
    MarkTerminatingResult,
    SweptSessionInfo,
    TerminatingKernelWithAgentData,
    TerminatingSessionData,
)
from .types.session_creation import (
    AllowedScalingGroup,
    SessionCreationContext,
    SessionCreationSpec,
    SessionEnqueueData,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

scheduler_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SCHEDULER_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class SchedulerRepository:
    """
    Repository that orchestrates between DB and cache sources for scheduling operations.
    """

    _db_source: ScheduleDBSource
    _cache_source: ScheduleCacheSource
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        valkey_stat: ValkeyStatClient,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db_source = ScheduleDBSource(db)
        self._cache_source = ScheduleCacheSource(valkey_stat)
        self._config_provider = config_provider

    @scheduler_repository_resilience.apply()
    async def get_scheduling_data(self, scaling_group: str) -> SchedulingData | None:
        """
        Get scheduling data from database.
        Returns None if no pending sessions exist.
        Raises ScalingGroupNotFound if scaling group doesn't exist.
        """
        known_slot_types = await self._get_known_slot_types()
        max_container_count = await self._get_max_container_count()
        spec = SchedulingSpec(
            known_slot_types=known_slot_types,
            max_container_count=max_container_count,
        )

        scheduling_data = await self._db_source.get_scheduling_data(scaling_group, spec)
        if not scheduling_data.pending_sessions.sessions:
            return None

        return scheduling_data

    @scheduler_repository_resilience.apply()
    async def allocate_sessions(
        self, allocation_batch: AllocationBatch
    ) -> list[ScheduledSessionData]:
        """
        Allocate sessions by updating DB.
        Agent occupied slots are synced directly in the DB.

        Returns:
            List of ScheduledSessionData for allocated sessions
        """
        return await self._db_source.allocate_sessions(allocation_batch)

    @scheduler_repository_resilience.apply()
    async def get_pending_timeout_sessions_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> list[SweptSessionInfo]:
        """
        Get sessions that have exceeded their pending timeout from given session IDs.
        Used by SweepSessionsLifecycleHandler for scaling group based processing.
        """
        return await self._db_source.get_pending_timeout_sessions_by_ids(session_ids)

    @scheduler_repository_resilience.apply()
    async def mark_sessions_terminating(
        self, session_ids: list[SessionId], reason: str = "USER_REQUESTED"
    ) -> MarkTerminatingResult:
        """
        Mark sessions for termination.
        """
        # Delegate to DB source
        return await self._db_source.mark_sessions_terminating(session_ids, reason)

    @scheduler_repository_resilience.apply()
    async def get_schedulable_scaling_groups(self) -> list[str]:
        """
        Get list of scaling groups that have schedulable agents.
        For sokovan scheduler compatibility.
        """
        return await self._db_source.get_schedulable_scaling_groups()

    @scheduler_repository_resilience.apply()
    async def get_terminating_sessions_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> list[TerminatingSessionData]:
        """
        Get terminating sessions by session IDs.

        This method is used by handlers that need detailed session data
        (TerminatingSessionData) beyond what the coordinator provides (HandlerSessionData).

        :param session_ids: List of session IDs to fetch
        :return: List of TerminatingSessionData objects with kernel details
        """
        return await self._db_source.get_terminating_sessions_by_ids(session_ids)

    @scheduler_repository_resilience.apply()
    async def get_terminating_kernels_with_lost_agents_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> list[TerminatingKernelWithAgentData]:
        """
        Get kernels in TERMINATING sessions that have lost or missing agents
        from given session IDs.
        Used by SweepLostAgentKernelsLifecycleHandler for scaling group based processing.
        """
        return await self._db_source.get_terminating_kernels_with_lost_agents_by_ids(session_ids)

    async def _get_known_slot_types(self) -> Mapping[SlotName, SlotTypes]:
        """
        Get known slot types from configuration.
        """
        return await self._config_provider.legacy_etcd_config_loader.get_resource_slots()

    async def _get_max_container_count(self) -> int | None:
        """
        Get max container count from configuration.
        """
        raw_value = await self._config_provider.legacy_etcd_config_loader.get_raw(
            "config/agent/max-container-count"
        )
        return int(raw_value) if raw_value else None

    @scheduler_repository_resilience.apply()
    async def enqueue_session(
        self,
        session_data: SessionEnqueueData,
    ) -> SessionId:
        """
        Enqueue a new session with its kernels.

        Args:
            session_data: Prepared session data with kernels and dependencies

        Returns:
            SessionId: The ID of the created session
        """
        return await self._db_source.enqueue_session(session_data)

    @scheduler_repository_resilience.apply()
    async def fetch_session_creation_data(
        self,
        spec: SessionCreationSpec,
        scaling_group_name: str,
        storage_manager: StorageSessionManager,
        allowed_vfolder_types: list[str],
    ) -> SessionCreationContext:
        """
        Fetch all data needed for session creation in a single DB session.

        Args:
            spec: Session creation specification
            scaling_group_name: Name of the scaling group
            storage_manager: Storage session manager
            allowed_vfolder_types: Allowed vfolder types from config

        Returns:
            SessionCreationContext with all required data
        """
        return await self._db_source.fetch_session_creation_data(
            spec, scaling_group_name, storage_manager, allowed_vfolder_types
        )

    @scheduler_repository_resilience.apply()
    async def fetch_session_creation_context(
        self,
        spec: SessionCreationSpec,
        scaling_group_name: str,
    ) -> SessionCreationContext:
        """
        Legacy method for backward compatibility.
        Use fetch_session_creation_data instead.

        Args:
            spec: Session creation specification
            scaling_group_name: Name of the scaling group

        Returns:
            SessionCreationContext with all required data
        """
        return await self._db_source.fetch_session_creation_context(spec, scaling_group_name)

    @scheduler_repository_resilience.apply()
    async def query_allowed_scaling_groups(
        self,
        domain_name: str,
        group_id: str,
        access_key: str,
    ) -> list[AllowedScalingGroup]:
        """
        Query allowed scaling groups for a user.

        Args:
            domain_name: Domain name
            group_id: Group ID
            access_key: Access key

        Returns:
            List of AllowedScalingGroup objects
        """
        return await self._db_source.query_allowed_scaling_groups(domain_name, group_id, access_key)

    @scheduler_repository_resilience.apply()
    async def prepare_vfolder_mounts(
        self,
        storage_manager: StorageSessionManager,
        allowed_vfolder_types: list[str],
        user_scope: UserScope,
        resource_policy: dict,
        combined_mounts: list,
        combined_mount_map: dict,
        requested_mount_options: dict,
    ) -> list[VFolderMount]:
        """
        Prepare vfolder mounts for the session.
        """
        return await self._db_source.prepare_vfolder_mounts(
            storage_manager,
            allowed_vfolder_types,
            user_scope,
            resource_policy,
            combined_mounts,
            combined_mount_map,
            requested_mount_options,
        )

    @scheduler_repository_resilience.apply()
    async def prepare_dotfiles(
        self,
        user_scope: UserScope,
        access_key: AccessKey,
        vfolder_mounts: list[VFolderMount],
    ) -> dict:
        """
        Prepare dotfile data for the session.
        """
        return await self._db_source.prepare_dotfiles(
            user_scope,
            access_key,
            vfolder_mounts,
        )

    @scheduler_repository_resilience.apply()
    async def check_available_image(
        self, image_identifier: ImageIdentifier, domain: str, user_uuid: UUID
    ) -> None:
        """
        Check if the specified image is available.
        Raises ImageNotFound if the image does not exist.
        """
        await self._db_source.check_available_image(image_identifier, domain, user_uuid)

    @scheduler_repository_resilience.apply()
    async def update_sessions_to_running(self, sessions_data: list[SessionRunningData]) -> None:
        """
        Update sessions from CREATING to RUNNING state with occupying_slots.
        """
        await self._db_source.update_sessions_to_running(sessions_data)

    @scheduler_repository_resilience.apply()
    async def update_kernels_to_pulling_for_image(
        self, agent_id: AgentId, image: str, image_ref: str | None = None
    ) -> int:
        """
        Update kernel status from PREPARING to PULLING for the specified image on an agent.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference
        :return: Number of kernels updated
        """
        return await self._db_source.update_kernels_to_pulling_for_image(agent_id, image, image_ref)

    @scheduler_repository_resilience.apply()
    async def update_kernels_to_prepared_for_image(
        self, agent_id: AgentId, image: str, image_ref: str | None = None
    ) -> int:
        """
        Update kernel status to PREPARED for the specified image on an agent.
        Updates kernels in both PULLING and PREPARING states.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference
        :return: Number of kernels updated
        """
        return await self._db_source.update_kernels_to_prepared_for_image(
            agent_id, image, image_ref
        )

    @scheduler_repository_resilience.apply()
    async def cancel_kernels_for_failed_image(
        self, agent_id: AgentId, image: str, error_msg: str, image_ref: str | None = None
    ) -> set[SessionId]:
        """
        Cancel kernels for an image that failed to be available on an agent.
        Also checks and cancels sessions if all their kernels are cancelled.

        :param agent_id: The agent ID where the image is unavailable
        :param image: The image name that failed
        :param error_msg: The error message to include in status
        :param image_ref: Optional image reference
        :return: Set of affected session IDs
        """
        affected_session_ids = await self._db_source.cancel_kernels_for_failed_image(
            agent_id, image, error_msg, image_ref
        )

        # Check if any sessions need to be cancelled
        for session_id in affected_session_ids:
            await self._db_source.check_and_cancel_session_if_needed(session_id)

        return affected_session_ids

    @scheduler_repository_resilience.apply()
    async def check_and_cancel_session_if_needed(self, session_id: SessionId) -> bool:
        """
        Check if a session should be cancelled when all its kernels are cancelled.

        :param session_id: The session ID to check
        :return: True if session was cancelled, False otherwise
        """
        return await self._db_source.check_and_cancel_session_if_needed(session_id)

    @scheduler_repository_resilience.apply()
    async def update_kernel_status_pulling(self, kernel_id: UUID, reason: str) -> bool:
        """Update kernel status to PULLING."""
        return await self._db_source.update_kernel_status_pulling(kernel_id, reason)

    @scheduler_repository_resilience.apply()
    async def update_kernel_status_creating(self, kernel_id: UUID, reason: str) -> bool:
        """Update kernel status to CREATING."""
        return await self._db_source.update_kernel_status_creating(kernel_id, reason)

    @scheduler_repository_resilience.apply()
    async def update_kernel_status_running(
        self, kernel_id: UUID, reason: str, creation_info: KernelCreationInfo
    ) -> bool:
        """Update kernel status to RUNNING."""
        return await self._db_source.update_kernel_status_running(kernel_id, reason, creation_info)

    @scheduler_repository_resilience.apply()
    async def update_kernel_status_preparing(self, kernel_id: UUID) -> bool:
        """Update kernel status to PREPARING."""
        return await self._db_source.update_kernel_status_preparing(kernel_id)

    @scheduler_repository_resilience.apply()
    async def update_kernel_status_cancelled(self, kernel_id: UUID, reason: str) -> bool:
        """Update kernel status to CANCELLED."""
        return await self._db_source.update_kernel_status_cancelled(kernel_id, reason)

    @scheduler_repository_resilience.apply()
    async def update_kernel_status_terminated(
        self, kernel_id: UUID, reason: str, exit_code: int | None = None
    ) -> bool:
        """Update kernel status to TERMINATED."""
        return await self._db_source.update_kernel_status_terminated(kernel_id, reason, exit_code)

    @scheduler_repository_resilience.apply()
    async def reset_kernels_to_pending_for_sessions(
        self, session_ids: list[SessionId], reason: str
    ) -> int:
        """Reset kernels to PENDING for the given sessions when max retries exceeded."""
        return await self._db_source.reset_kernels_to_pending_for_sessions(session_ids, reason)

    @scheduler_repository_resilience.apply()
    async def update_kernels_to_creating_for_sessions(
        self, session_ids: list[SessionId], reason: str
    ) -> int:
        """Update kernels to CREATING for the given sessions when session starts creating."""
        return await self._db_source.update_kernels_to_creating_for_sessions(session_ids, reason)

    @scheduler_repository_resilience.apply()
    async def update_kernels_to_terminated(self, kernel_ids: list[str], reason: str) -> int:
        """Update multiple kernels to TERMINATED status."""
        return await self._db_source.update_kernels_to_terminated(kernel_ids, reason)

    @scheduler_repository_resilience.apply()
    async def get_sessions_for_pull(
        self,
        statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus],
    ) -> SessionsForPullWithImages:
        """
        Get sessions for image pulling with specified statuses.
        Returns SessionsForPullWithImages dataclass.

        :param statuses: Session statuses to filter by (typically SCHEDULED, PREPARING, PULLING)
        :param kernel_statuses: Kernel statuses to filter by (typically PREPARED, PULLING)
        :return: SessionsForPullWithImages object
        """
        return await self._db_source.get_sessions_for_pull(statuses, kernel_statuses)

    @scheduler_repository_resilience.apply()
    async def get_sessions_for_pull_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> SessionsForPullWithImages:
        """
        Get sessions for image pulling by session IDs.

        This method is used by handlers that need additional session data
        (SessionDataForPull and ImageConfigData) beyond what the coordinator
        provides (HandlerSessionData).

        :param session_ids: List of session IDs to fetch
        :return: SessionsForPullWithImages object with sessions and image configs
        """
        return await self._db_source.get_sessions_for_pull_by_ids(session_ids)

    @scheduler_repository_resilience.apply()
    async def get_sessions_for_start(
        self,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus],
    ) -> SessionsForStartWithImages:
        """
        Get sessions for starting with specified statuses.
        Returns SessionsForStartWithImages dataclass.

        :param statuses: Session statuses to filter by (typically PREPARED, CREATING)
        :param kernel_statuses: Kernel statuses to filter by (typically PREPARED)
        :return: SessionsForStartWithImages object
        """
        return await self._db_source.get_sessions_for_start(session_statuses, kernel_statuses)

    @scheduler_repository_resilience.apply()
    async def get_sessions_for_start_by_ids(
        self,
        session_ids: list[SessionId],
    ) -> SessionsForStartWithImages:
        """
        Get sessions for starting by session IDs.

        This method is used by handlers that need additional session data
        (SessionDataForStart and ImageConfigData) beyond what the coordinator
        provides (HandlerSessionData).

        :param session_ids: List of session IDs to fetch
        :return: SessionsForStartWithImages object with sessions and image configs
        """
        return await self._db_source.get_sessions_for_start_by_ids(session_ids)

    @scheduler_repository_resilience.apply()
    async def mark_session_cancelled(
        self, session_id: SessionId, error_info: ErrorStatusInfo, reason: str = "FAILED_TO_START"
    ) -> None:
        """
        Mark a session as cancelled with error information.
        """
        await self._db_source.mark_session_cancelled(session_id, error_info, reason)

    @scheduler_repository_resilience.apply()
    async def get_container_info_for_kernels(self, session_id: SessionId) -> dict[UUID, str | None]:
        """
        Get container IDs for kernels in a session.
        """
        return await self._db_source.get_container_info_for_kernels(session_id)

    @scheduler_repository_resilience.apply()
    async def update_session_error_info(
        self, session_id: SessionId, error_info: ErrorStatusInfo
    ) -> None:
        """
        Update session's status_data with error information without changing status.
        This is used when a session fails but should be retried later.

        :param session_id: The session ID to update
        :param error_info: Error information to store in status_data
        """
        await self._db_source.update_session_error_info(session_id, error_info)

    @scheduler_repository_resilience.apply()
    async def get_keypair_concurrency(self, access_key: AccessKey, is_sftp: bool = False) -> int:
        """
        Get keypair concurrency with cache-through pattern.
        First checks cache, falls back to DB if not cached, and updates cache.

        :param access_key: The access key to query
        :param is_sftp: Whether to get SFTP concurrency (True) or regular concurrency (False)
        :return: Current concurrency count
        """
        # Try to get from cache first
        try:
            cached_value = await self._cache_source.get_keypair_concurrency(access_key, is_sftp)
            if cached_value is not None:
                return cached_value
        except Exception as e:
            log.warning(
                "Failed to get keypair concurrency from cache for {}: {}",
                access_key,
                e,
            )

        # Cache miss - refresh both values from DB
        concurrency_data = await self._db_source.get_keypair_concurrencies_from_db(access_key)

        # Update cache with both values at once
        try:
            await self._cache_source.set_keypair_concurrencies(
                access_key,
                concurrency_data.regular_count,
                concurrency_data.sftp_count,
            )
        except Exception as e:
            log.warning(
                "Failed to update keypair concurrency cache for {}: {}",
                access_key,
                e,
            )

        # Return the requested value
        return concurrency_data.sftp_count if is_sftp else concurrency_data.regular_count

    @scheduler_repository_resilience.apply()
    async def invalidate_kernel_related_cache(self, access_keys: list[AccessKey]) -> None:
        """
        Invalidate caches related to kernel state changes affecting resource calculations.

        :param access_keys: List of access keys whose related caches should be invalidated
        """
        await self._cache_source.invalidate_kernel_related_cache(access_keys)

    @scheduler_repository_resilience.apply()
    async def update_session_network_id(
        self,
        session_id: SessionId,
        network_id: str | None,
    ) -> None:
        """
        Update the network ID associated with a session.
        :param session_id: The session ID to update
        :param network_id: The new network ID to set (or None to clear)
        """
        await self._db_source.update_session_network_id(
            session_id,
            network_id,
        )

    @scheduler_repository_resilience.apply()
    async def get_total_resource_slots(self) -> TotalResourceData:
        """
        Get total resource slots from all agents.
        Uses cache-through pattern: checks cache first, falls back to DB calculation,
        and updates cache.

        :return: TotalResourceData with total used, free, and capable slots
        """
        # Try to get from cache first
        try:
            cached_data = await self._cache_source.get_total_resource_slots()
            if cached_data is not None:
                return cached_data
        except Exception as e:
            log.warning("Failed to get total resource slots from cache: {}", e)

        # Cache miss - calculate from DB
        total_resource_data = await self._db_source.calculate_total_resource_slots()

        # Update cache with calculated value
        try:
            await self._cache_source.set_total_resource_slots(total_resource_data)
        except Exception as e:
            log.warning("Failed to update total resource slots cache: {}", e)

        return total_resource_data

    # =========================================================================
    # Handler-specific methods for SessionLifecycleHandler pattern
    # =========================================================================

    @scheduler_repository_resilience.apply()
    async def get_sessions_for_handler(
        self,
        scaling_group: str,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus] | None,
    ) -> list[SessionWithKernels]:
        """Get sessions for handler execution based on status filters.

        This method is used by SessionLifecycleHandler implementations.
        The coordinator calls this to query sessions before passing to handlers.

        For SessionPromotionHandler (ALL/ANY/NOT_ANY conditions), use
        get_sessions_for_promotion() instead.

        Uses SessionInfo and KernelInfo types for unified data representation.

        Args:
            scaling_group: The scaling group to filter by (first parameter for consistency)
            session_statuses: Session statuses to include
            kernel_statuses: Kernel statuses to filter by. If non-None, includes sessions
                           that have at least one kernel in these statuses (simple filtering).
                           If None, includes all sessions regardless of kernel status.

        Returns:
            List of SessionWithKernels containing SessionInfo and KernelInfo objects.
        """
        return await self._db_source.fetch_sessions_for_handler(
            scaling_group, session_statuses, kernel_statuses
        )

    @scheduler_repository_resilience.apply()
    async def search_kernels_for_handler(
        self,
        querier: BatchQuerier,
    ) -> KernelListResult:
        """Search kernels for kernel handler execution.

        This method is used by KernelLifecycleHandler implementations.
        The coordinator calls this to query kernels using BatchQuerier.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Use KernelConditions for filtering by status, scaling_group, etc.

        Returns:
            KernelListResult containing KernelInfo objects with pagination info.
        """
        return await self._db_source.search_kernels_for_handler(querier)

    @scheduler_repository_resilience.apply()
    async def update_with_history(
        self,
        updater: BatchUpdater[SessionRow],
        bulk_creator: BulkCreator[SessionSchedulingHistoryRow],
    ) -> int:
        """Update session statuses and record history in same transaction.

        This method combines batch status update with history recording,
        ensuring both operations are atomic within a single transaction.

        Args:
            updater: BatchUpdater containing spec and conditions for session update
            bulk_creator: BulkCreator containing specs for history records

        Returns:
            Number of sessions updated
        """
        return await self._db_source.update_with_history(updater, bulk_creator)

    @scheduler_repository_resilience.apply()
    async def create_scheduling_history(
        self,
        bulk_creator: BulkCreator[SessionSchedulingHistoryRow],
    ) -> int:
        """Create scheduling history records without status update.

        Used for recording skipped sessions where no status change occurs
        but the scheduling attempt should be recorded in history.

        Args:
            bulk_creator: BulkCreator containing specs for history records

        Returns:
            Number of history records created
        """
        return await self._db_source.create_scheduling_history(bulk_creator)

    # ========================================================================
    # Search methods (BatchQuerier pattern)
    # ========================================================================

    @scheduler_repository_resilience.apply()
    async def search_sessions_with_kernels(
        self,
        querier: BatchQuerier,
    ) -> SessionWithKernelsSearchResult:
        """Search sessions with kernel data and image configs.

        Returns session data with full kernel details and resolved image configs.
        Use this when kernel binding information is needed (e.g., image pulling).

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Use NoPagination for scheduler batch operations.

        Returns:
            SessionWithKernelsSearchResult with sessions, image_configs, and pagination info
        """
        return await self._db_source.search_sessions_with_kernels(querier)

    @scheduler_repository_resilience.apply()
    async def search_sessions_with_kernels_and_user(
        self,
        querier: BatchQuerier,
    ) -> SessionWithKernelsAndUserSearchResult:
        """Search sessions with kernel data, user info, and image configs.

        Returns session data with full kernel details, user information, and
        resolved image configs. Use this when starting sessions.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Use NoPagination for scheduler batch operations.

        Returns:
            SessionWithKernelsAndUserSearchResult with sessions, image_configs, and pagination info
        """
        return await self._db_source.search_sessions_with_kernels_and_user(querier)

    @scheduler_repository_resilience.apply()
    async def search_sessions_with_kernels_for_handler(
        self,
        querier: BatchQuerier,
    ) -> list[SessionWithKernels]:
        """Search sessions with their kernels using SessionInfo/KernelInfo for handlers.

        This method uses the unified SessionInfo and KernelInfo types,
        providing full session and kernel data for handler execution.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Conditions should target SessionRow columns.

        Returns:
            List of SessionWithKernels containing SessionInfo and KernelInfo objects.
        """
        return await self._db_source.search_sessions_with_kernels_for_handler(querier)

    @scheduler_repository_resilience.apply()
    async def search_sessions_for_handler(
        self,
        querier: BatchQuerier,
    ) -> list[SessionInfo]:
        """Search sessions without kernel data for handlers.

        This method returns only session data without loading kernels,
        optimized for handlers that don't need kernel information.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.
                     Conditions should target SessionRow columns.
                     Use kernel EXISTS subquery conditions for filtering
                     (e.g., SessionConditions.all_kernels_in_statuses).

        Returns:
            List of SessionInfo objects.
        """
        return await self._db_source.search_sessions_for_handler(querier)

    @scheduler_repository_resilience.apply()
    async def get_last_session_histories(
        self,
        session_ids: list[SessionId],
    ) -> dict[SessionId, SessionSchedulingHistoryRow]:
        """Get last history records for multiple sessions.

        Returns the most recent history record for each session. The caller
        should compare history.phase with the current phase to determine
        if attempts should be used or reset to 0.

        Args:
            session_ids: List of session IDs to fetch history for

        Returns:
            Dict mapping session_id to latest history record
        """
        return await self._db_source.get_last_session_histories(session_ids)

    @scheduler_repository_resilience.apply()
    async def lower_session_priority(
        self,
        session_ids: list[SessionId],
        amount: int,
        min_priority: int,
    ) -> None:
        """Lower the priority of sessions by a specified amount with a floor.

        Used when sessions exceed max scheduling retries (give_up) and need to be
        deprioritized before returning to PENDING for re-scheduling.

        Args:
            session_ids: List of session IDs to update
            amount: Amount to subtract from current priority
            min_priority: Minimum priority floor (priority will not go below this)
        """
        await self._db_source.lower_session_priority(session_ids, amount, min_priority)

    async def update_kernels_last_observed_at(
        self,
        kernel_observation_times: Mapping[UUID, datetime],
    ) -> int:
        """Update the last_observed_at timestamp for multiple kernels.

        Used by fair share observer to record when kernels were last observed
        for resource usage tracking. Each kernel can have a different observation
        time (e.g., terminated kernels use terminated_at, running kernels use now).

        Args:
            kernel_observation_times: Mapping of kernel ID to observation timestamp

        Returns:
            Number of kernels updated
        """
        return await self._db_source.update_kernels_last_observed_at(kernel_observation_times)

    async def get_db_now(self) -> datetime:
        """Get the current timestamp from the database.

        Used for consistent time handling across HA environments
        where server clocks may differ.

        Returns:
            Current database timestamp with timezone
        """
        return await self._db_source.get_db_now()
