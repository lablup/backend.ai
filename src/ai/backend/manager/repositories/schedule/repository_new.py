"""Repository pattern implementation for schedule operations."""

import logging
from typing import Mapping, Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import SessionId, SlotName, SlotTypes
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .cache_source.cache_source import ScheduleCacheSource
from .db_source.db_source import ScheduleDBSource
from .types.allocation import AllocationBatch
from .types.base import SchedulingSpec
from .types.scheduling import SchedulingData
from .types.session import (
    MarkTerminatingResult,
    SessionTerminationResult,
    SweptSessionInfo,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


schedule_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.SCHEDULE_REPOSITORY)),
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

    @schedule_repository_resilience.apply()
    async def get_scheduling_data(self, scaling_group: str) -> Optional[SchedulingData]:
        """
        Get scheduling data from database.
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
        scheduling_data = await self._db_source.get_scheduling_data(scaling_group, spec)
        if not scheduling_data.pending_sessions.sessions:
            return None

        return scheduling_data

    @schedule_repository_resilience.apply()
    async def allocate_sessions(self, allocation_batch: AllocationBatch) -> None:
        """
        Allocate sessions by updating DB.
        Agent occupied slots are synced directly in the DB.
        """
        # Update DB
        await self._db_source.allocate_sessions(allocation_batch)

    @schedule_repository_resilience.apply()
    async def get_pending_timeout_sessions(self) -> list[SweptSessionInfo]:
        """
        Get sessions that have exceeded their pending timeout.
        The timeout is determined by each scaling group's scheduler_opts.
        """
        # Fetch from DB source
        return await self._db_source.get_pending_timeout_sessions()

    @schedule_repository_resilience.apply()
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

        # Update DB
        await self._db_source.batch_update_terminated_status(session_results)

    @schedule_repository_resilience.apply()
    async def mark_sessions_terminating(
        self, session_ids: list[SessionId], reason: str = "USER_REQUESTED"
    ) -> MarkTerminatingResult:
        """
        Mark sessions for termination.
        """
        # Delegate to DB source
        return await self._db_source.mark_sessions_terminating(session_ids, reason)

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
