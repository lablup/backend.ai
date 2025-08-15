"""Repository pattern implementation for schedule operations."""

import logging
from collections import defaultdict
from datetime import timedelta
from typing import Mapping, Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import AccessKey, AgentId, ResourceSlot, SlotName, SlotTypes
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models import PRIVATE_SESSION_TYPES
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.sokovan.scheduler.types import AllocationBatch

from .cache_source.cache_source import ScheduleCacheSource
from .db_source.db_source import ScheduleDBSource
from .db_source.types import SchedulingSpec
from .entity import (
    MarkTerminatingResult,
    SchedulingContextData,
    SessionTerminationResult,
    SweptSessionInfo,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScheduleRepository:
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

    async def get_scheduling_context_data(
        self, scaling_group: str
    ) -> Optional[SchedulingContextData]:
        """
        Get scheduling context data by combining DB and cache sources.
        Returns None if no pending sessions exist.
        Raises ScalingGroupNotFound if scaling group doesn't exist.
        """
        # Get scheduling specification
        known_slot_types = await self._get_known_slot_types()
        max_container_count = await self._get_max_container_count()
        spec = SchedulingSpec(
            known_slot_types=known_slot_types,
            max_container_count=max_container_count,
        )

        # Fetch data from DB (will raise ScalingGroupNotFound if not found)
        db_data = await self._db_source.get_scheduling_data(scaling_group, spec)
        if not db_data.pending_sessions.sessions:
            return None

        # Transform to entity using the data class's transformation method
        return db_data.to_scheduling_context()

    async def allocate_sessions(self, allocation_batch: AllocationBatch) -> None:
        """
        Allocate sessions by updating DB and cache.
        """
        # Track concurrency changes
        concurrency_to_increment: dict[AccessKey, int] = defaultdict(int)
        sftp_concurrency_to_increment: dict[AccessKey, int] = defaultdict(int)

        # Process allocations
        for allocation in allocation_batch.allocations:
            if allocation.session_type.is_private():
                sftp_concurrency_to_increment[allocation.access_key] += 1
            else:
                concurrency_to_increment[allocation.access_key] += 1

        # Update DB (includes agent resource allocation and status updates)
        await self._db_source.allocate_sessions(allocation_batch)

        # Update cache concurrency
        await self._cache_source.increment_concurrencies(
            concurrency_to_increment, sftp_concurrency_to_increment
        )

    async def get_pending_timeout_sessions(self) -> list[SweptSessionInfo]:
        """
        Get sessions that have exceeded their pending timeout.
        """
        # Get default timeout from config
        default_timeout = timedelta(seconds=0)  # Or fetch from config if needed

        # Fetch from DB source
        db_swept_sessions = await self._db_source.get_pending_timeout_sessions(default_timeout)

        # Transform to entities
        return [s.to_swept_session_info() for s in db_swept_sessions]

    async def batch_update_terminated_status(
        self,
        session_results: list[SessionTerminationResult],
    ) -> None:
        """
        Update terminated status in DB and cache.
        """
        if not session_results:
            return

        # Track concurrency changes and agent resources to free
        concurrency_to_decrement: dict[AccessKey, int] = defaultdict(int)
        sftp_concurrency_to_decrement: dict[AccessKey, int] = defaultdict(int)
        agent_slots_to_free: dict[AgentId, ResourceSlot] = defaultdict(ResourceSlot)

        # Process results
        for session_result in session_results:
            # Track resources to free
            for kernel in session_result.kernel_results:
                if kernel.success and kernel.agent_id:
                    agent_slots_to_free[kernel.agent_id] += kernel.occupied_slots

            # Track concurrency decrements for successfully terminated sessions
            if session_result.should_terminate_session:
                if session_result.session_type in PRIVATE_SESSION_TYPES:
                    sftp_concurrency_to_decrement[session_result.access_key] += 1
                else:
                    concurrency_to_decrement[session_result.access_key] += 1

        # Update DB
        await self._db_source.batch_update_terminated_status(session_results, agent_slots_to_free)

        # Update cache
        await self._cache_source.decrement_concurrencies(
            concurrency_to_decrement, sftp_concurrency_to_decrement
        )

    async def mark_sessions_terminating(
        self, session_ids: list[str], reason: str = "USER_REQUESTED"
    ) -> MarkTerminatingResult:
        """
        Mark sessions for termination.
        """
        # Delegate to DB source
        db_result = await self._db_source.mark_sessions_terminating(session_ids, reason)
        # Transform to entity
        return db_result.to_mark_terminating_result()

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
