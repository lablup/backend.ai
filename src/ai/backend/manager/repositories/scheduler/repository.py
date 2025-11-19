"""Repository pattern implementation for schedule operations."""

from __future__ import annotations

import logging
from typing import Mapping, Optional
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
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
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.exceptions import ErrorStatusInfo
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.scheduler.results import ScheduledSessionData
from ai.backend.manager.sokovan.scheduler.types import (
    AllocationBatch,
    KernelCreationInfo,
    SessionRunningData,
    SessionsForPullWithImages,
    SessionsForStartWithImages,
    SessionTransitionData,
)

from .cache_source.cache_source import ScheduleCacheSource
from .db_source.db_source import ScheduleDBSource
from .types.base import SchedulingSpec
from .types.scheduling import SchedulingData
from .types.session import (
    KernelTerminationResult,
    MarkTerminatingResult,
    SessionTerminationResult,
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
    ):
        self._db_source = ScheduleDBSource(db)
        self._cache_source = ScheduleCacheSource(valkey_stat)
        self._config_provider = config_provider

    async def get_scheduling_data(self, scaling_group: str) -> Optional[SchedulingData]:
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

    async def get_pending_timeout_sessions(self) -> list[SweptSessionInfo]:
        """
        Get sessions that have exceeded their pending timeout.
        The timeout is determined by each scaling group's scheduler_opts.
        """
        return await self._db_source.get_pending_timeout_sessions()

    async def batch_update_terminated_status(
        self,
        session_results: list[SessionTerminationResult],
    ) -> None:
        """
        Update terminated status in DB.
        Agent occupied slots are synced directly in the DB.
        """
        if not session_results:
            return

        await self._db_source.batch_update_terminated_status(session_results)

    async def batch_update_kernels_terminated(
        self,
        kernel_results: list[KernelTerminationResult],
        reason: str,
    ) -> None:
        """
        Update kernel statuses to TERMINATED without updating session status.
        Agent occupied slots are synced directly in the DB.
        """
        if not kernel_results:
            return

        await self._db_source.batch_update_kernels_terminated(kernel_results, reason)

    async def mark_sessions_terminating(
        self, session_ids: list[SessionId], reason: str = "USER_REQUESTED"
    ) -> MarkTerminatingResult:
        """
        Mark sessions for termination.
        """
        # Delegate to DB source
        return await self._db_source.mark_sessions_terminating(session_ids, reason)

    async def get_schedulable_scaling_groups(self) -> list[str]:
        """
        Get list of scaling groups that have schedulable agents.
        For sokovan scheduler compatibility.
        """
        return await self._db_source.get_schedulable_scaling_groups()

    async def get_terminating_sessions(self) -> list[TerminatingSessionData]:
        """
        Get sessions with TERMINATING status.
        For sokovan scheduler compatibility.
        """
        return await self._db_source.get_terminating_sessions()

    async def get_terminating_kernels_with_lost_agents(
        self,
    ) -> list[TerminatingKernelWithAgentData]:
        """
        Get kernels in TERMINATING sessions that have lost or missing agents.
        For lost agent cleanup operations.
        """
        return await self._db_source.get_terminating_kernels_with_lost_agents()

    async def _get_known_slot_types(self) -> Mapping[SlotName, SlotTypes]:
        """
        Get known slot types from configuration.
        """
        return await self._config_provider.legacy_etcd_config_loader.get_resource_slots()

    async def _get_max_container_count(self) -> Optional[int]:
        """
        Get max container count from configuration.
        """
        raw_value = await self._config_provider.legacy_etcd_config_loader.get_raw(
            "config/agent/max-container-count"
        )
        return int(raw_value) if raw_value else None

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

    async def fetch_session_creation_data(
        self,
        spec: SessionCreationSpec,
        scaling_group_name: str,
        storage_manager,
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

    async def prepare_vfolder_mounts(
        self,
        storage_manager,
        allowed_vfolder_types: list[str],
        user_scope,
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

    async def prepare_dotfiles(
        self,
        user_scope,
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

    async def check_available_image(
        self, image_identifier: ImageIdentifier, domain: str, user_uuid: UUID
    ) -> None:
        """
        Check if the specified image is available.
        Raises ImageNotFound if the image does not exist.
        """
        await self._db_source.check_available_image(image_identifier, domain, user_uuid)

    async def update_sessions_to_prepared(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions from PULLING or PREPARING to PREPARED state.
        """
        await self._db_source.update_sessions_to_prepared(session_ids)

    async def get_sessions_ready_to_run(self) -> list[SessionId]:
        """
        Get sessions in CREATING state where all kernels are RUNNING.
        These sessions are ready to transition to RUNNING state.
        """
        return await self._db_source.get_sessions_ready_to_run()

    async def get_sessions_for_transition(
        self,
        session_statuses: list[SessionStatus],
        kernel_statuses: list[KernelStatus],
    ) -> list[SessionTransitionData]:
        """
        Get sessions ready for state transition based on current session and kernel status.

        :param session_statuses: List of current session statuses to filter by
        :param kernel_statuses: List of current kernel statuses to filter by
        :return: List of sessions ready for transition with detailed information
        """
        return await self._db_source.get_sessions_for_transition(session_statuses, kernel_statuses)

    async def update_sessions_to_running(self, sessions_data: list[SessionRunningData]) -> None:
        """
        Update sessions from CREATING to RUNNING state with occupying_slots.
        """
        await self._db_source.update_sessions_to_running(sessions_data)

    async def get_sessions_ready_to_terminate(self) -> list[SessionId]:
        """
        Get sessions in TERMINATING state where all kernels are TERMINATED.
        These sessions are ready to transition to TERMINATED state.
        """
        return await self._db_source.get_sessions_ready_to_terminate()

    async def update_sessions_to_terminated(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions from TERMINATING to TERMINATED state.
        """
        await self._db_source.update_sessions_to_terminated(session_ids)

    async def update_kernels_to_pulling_for_image(
        self, agent_id: AgentId, image: str, image_ref: Optional[str] = None
    ) -> int:
        """
        Update kernel status from PREPARING to PULLING for the specified image on an agent.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference
        :return: Number of kernels updated
        """
        return await self._db_source.update_kernels_to_pulling_for_image(agent_id, image, image_ref)

    async def update_kernels_to_prepared_for_image(
        self, agent_id: AgentId, image: str, image_ref: Optional[str] = None
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

    async def cancel_kernels_for_failed_image(
        self, agent_id: AgentId, image: str, error_msg: str, image_ref: Optional[str] = None
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

    async def check_and_cancel_session_if_needed(self, session_id: SessionId) -> bool:
        """
        Check if a session should be cancelled when all its kernels are cancelled.

        :param session_id: The session ID to check
        :return: True if session was cancelled, False otherwise
        """
        return await self._db_source.check_and_cancel_session_if_needed(session_id)

    async def update_kernel_status_pulling(self, kernel_id: UUID, reason: str) -> bool:
        """Update kernel status to PULLING."""
        return await self._db_source.update_kernel_status_pulling(kernel_id, reason)

    async def update_kernel_status_creating(self, kernel_id: UUID, reason: str) -> bool:
        """Update kernel status to CREATING."""
        return await self._db_source.update_kernel_status_creating(kernel_id, reason)

    async def update_kernel_status_running(
        self, kernel_id: UUID, reason: str, creation_info: KernelCreationInfo
    ) -> bool:
        """Update kernel status to RUNNING."""
        return await self._db_source.update_kernel_status_running(kernel_id, reason, creation_info)

    async def update_kernel_status_preparing(self, kernel_id: UUID) -> bool:
        """Update kernel status to PREPARING."""
        return await self._db_source.update_kernel_status_preparing(kernel_id)

    async def update_kernel_status_cancelled(self, kernel_id: UUID, reason: str) -> bool:
        """Update kernel status to CANCELLED."""
        return await self._db_source.update_kernel_status_cancelled(kernel_id, reason)

    async def update_kernel_status_terminated(
        self, kernel_id: UUID, reason: str, exit_code: Optional[int] = None
    ) -> bool:
        """Update kernel status to TERMINATED."""
        return await self._db_source.update_kernel_status_terminated(kernel_id, reason, exit_code)

    async def update_kernel_heartbeat(self, kernel_id: UUID) -> bool:
        """Update kernel heartbeat timestamp."""
        return await self._db_source.update_kernel_heartbeat(kernel_id)

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

    async def update_sessions_to_preparing(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions from SCHEDULED to PREPARING status.
        """
        await self._db_source.update_sessions_to_preparing(session_ids)

    async def update_sessions_and_kernels_to_creating(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions and kernels from PREPARED to CREATING status.
        """
        await self._db_source.update_sessions_and_kernels_to_creating(session_ids)

    async def mark_session_cancelled(
        self, session_id: SessionId, error_info: ErrorStatusInfo, reason: str = "FAILED_TO_START"
    ) -> None:
        """
        Mark a session as cancelled with error information.
        """
        await self._db_source.mark_session_cancelled(session_id, error_info, reason)

    async def get_container_info_for_kernels(
        self, session_id: SessionId
    ) -> dict[UUID, Optional[str]]:
        """
        Get container IDs for kernels in a session.
        """
        return await self._db_source.get_container_info_for_kernels(session_id)

    async def batch_update_stuck_session_retries(
        self, session_ids: list[SessionId], max_retries: int = 5
    ) -> list[SessionId]:
        """
        Batch update retry counts for stuck sessions.
        Sessions that exceed max_retries are moved to PENDING status.

        :param session_ids: List of session IDs to update
        :param max_retries: Maximum retries before moving to PENDING (default: 5)
        :return: List of session IDs that should continue retrying (not moved to PENDING)
        """
        return await self._db_source.batch_update_stuck_session_retries(session_ids, max_retries)

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

    async def invalidate_kernel_related_cache(self, access_keys: list[AccessKey]) -> None:
        """
        Invalidate caches related to kernel state changes affecting resource calculations.

        :param access_keys: List of access keys whose related caches should be invalidated
        """
        await self._cache_source.invalidate_kernel_related_cache(access_keys)

    async def update_session_network_id(
        self,
        session_id: SessionId,
        network_id: Optional[str],
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
