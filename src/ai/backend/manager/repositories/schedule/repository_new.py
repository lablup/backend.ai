from typing import Optional

from ai.backend.manager.repositories.schedule.cache_source.cache_source import ScheduleCacheSource
from ai.backend.manager.repositories.schedule.db_source.db_source import ScheduleDBSource
from ai.backend.manager.repositories.schedule.repository import (
    SchedulingContextData,
    SessionTerminationResult,
    SweptSessionInfo,
)
from ai.backend.manager.sokovan.scheduler.types import AllocationBatch


class ScheduleRepository:
    _db_source: ScheduleDBSource
    _cache_source: ScheduleCacheSource

    def __init__(self, db_source: ScheduleDBSource, cache_source: ScheduleCacheSource):
        self._db_source = db_source
        self._cache_source = cache_source

    async def get_scheduling_context_data(
        self, scaling_group: str
    ) -> Optional[SchedulingContextData]:
        raise NotImplementedError("Method not implemented in ScheduleRepository")

    async def allocate_sessions(self, allocation_batch: AllocationBatch) -> None:
        """
        Allocate sessions based on the provided allocation batch.

        Args:
            allocation_batch: The batch of sessions to allocate.
        """
        # Implementation of session allocation logic
        raise NotImplementedError("Method not implemented in ScheduleRepository")

    async def get_pending_timeout_sessions(self) -> list[SweptSessionInfo]:
        """
        Retrieve a list of sessions that are pending timeout.

        Returns:
            A list of SweptSessionInfo objects representing sessions pending timeout.
        """
        # Implementation to fetch pending timeout sessions
        raise NotImplementedError("Method not implemented in ScheduleRepository")

    async def batch_update_terminated_status(
        self,
        session_results: list[SessionTerminationResult],
    ) -> None:
        """
        Batch update the status of terminated sessions.

        Args:
            session_results: List of SessionTerminationResult objects containing session IDs and their new status.
        """
        raise NotImplementedError("Method not implemented in ScheduleRepository")
