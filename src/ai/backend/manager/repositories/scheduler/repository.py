"""Repository pattern implementation for schedule operations."""

import logging
from typing import Mapping, Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import AccessKey, SessionId, SlotName, SlotTypes, VFolderMount
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.scheduler.types import AllocationBatch

from .cache_source.cache_source import ScheduleCacheSource
from .db_source.db_source import ScheduleDBSource
from .types.base import SchedulingSpec
from .types.scheduling import SchedulingData
from .types.session import (
    MarkTerminatingResult,
    SessionTerminationResult,
    SweptSessionInfo,
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

    async def allocate_sessions(self, allocation_batch: AllocationBatch) -> None:
        """
        Allocate sessions by updating DB.
        Agent occupied slots are synced directly in the DB.
        """
        await self._db_source.allocate_sessions(allocation_batch)

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

    async def get_terminating_sessions(self) -> list:
        """
        Get sessions with TERMINATING status.
        For sokovan scheduler compatibility.
        """
        return await self._db_source.get_terminating_sessions()

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

    async def get_sessions_ready_to_create(self) -> list[SessionId]:
        """
        Get sessions in PULLING state where all kernels have progressed past PULLING.
        These sessions are ready to transition to CREATING state.
        """
        return await self._db_source.get_sessions_ready_to_create()

    async def update_sessions_to_creating(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions from PULLING to CREATING state.
        """
        await self._db_source.update_sessions_to_creating(session_ids)

    async def get_sessions_ready_to_run(self) -> list[SessionId]:
        """
        Get sessions in CREATING/PREPARING state where all kernels are RUNNING.
        These sessions are ready to transition to RUNNING state.
        """
        return await self._db_source.get_sessions_ready_to_run()

    async def update_sessions_to_running(self, session_ids: list[SessionId]) -> None:
        """
        Update sessions from CREATING/PREPARING to RUNNING state.
        """
        await self._db_source.update_sessions_to_running(session_ids)

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
