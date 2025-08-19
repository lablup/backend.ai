"""Health monitor for managing session health checks."""

import logging
from typing import TYPE_CHECKING

from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.session import SessionStatus

from .handlers import (
    CreatingHealthKeeper,
    HealthKeeper,
    PullingHealthKeeper,
)
from .results import HealthCheckResult
from .types import SessionData

if TYPE_CHECKING:
    pass

from ai.backend.manager.clients.agent.pool import AgentPool
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository

log = BraceStyleAdapter(logging.getLogger(__name__))


class HealthMonitor:
    """
    Monitor for checking session health based on status.
    Uses handler pattern similar to sokovan scheduler.
    """

    _repository: ScheduleRepository
    _health_keepers: dict[SessionStatus, HealthKeeper]

    def __init__(
        self,
        repository: ScheduleRepository,
        agent_pool: AgentPool,
    ):
        self._repository = repository

        # Initialize keepers for each monitored status
        # PREPARING and PULLING share the same keeper
        pulling_keeper = PullingHealthKeeper(agent_pool)
        creating_keeper = CreatingHealthKeeper(agent_pool)

        self._health_keepers = {
            SessionStatus.PREPARING: pulling_keeper,
            SessionStatus.PULLING: pulling_keeper,
            SessionStatus.CREATING: creating_keeper,
        }

        log.info(
            "Health monitor initialized with keepers for statuses: {}",
            list(self._health_keepers.keys()),
        )

    async def check_sessions_batch(
        self,
        sessions: list[SessionData],
    ) -> HealthCheckResult:
        """Check health of multiple sessions in batch.

        Args:
            sessions: Sessions to check

        Returns:
            Aggregated health check result
        """
        # Group sessions by status
        sessions_by_status: dict[SessionStatus, list[SessionData]] = {}
        for session in sessions:
            if session.status in self._health_keepers:
                if session.status not in sessions_by_status:
                    sessions_by_status[session.status] = []
                sessions_by_status[session.status].append(session)

        # Process each status group with its keeper
        all_healthy: list[SessionId] = []
        all_unhealthy: list[SessionId] = []

        for status, status_sessions in sessions_by_status.items():
            keeper = self._health_keepers[status]
            log.debug(
                "Checking {} sessions with status {} using keeper {}",
                len(status_sessions),
                status,
                keeper.name(),
            )

            try:
                result = await keeper.handle_batch(status_sessions)
                all_healthy.extend(result.healthy_sessions)
                all_unhealthy.extend(result.unhealthy_sessions)
            except Exception as e:
                log.error(
                    "Error during health check for status {}: {}",
                    status,
                    e,
                )
                # On error, consider all sessions as unhealthy
                all_unhealthy.extend(session.id for session in status_sessions)

        return HealthCheckResult(
            healthy_sessions=all_healthy,
            unhealthy_sessions=all_unhealthy,
        )

    async def check_sessions_by_status(
        self,
        status: SessionStatus,
    ) -> HealthCheckResult:
        """Check health of all sessions with a specific status.

        Args:
            status: Status to filter sessions by

        Returns:
            Aggregated health check result
        """
        # TODO: Implement get_sessions_by_status in ScheduleRepository
        # For now, this is a placeholder - the actual implementation would
        # query sessions by status and convert them to SessionData
        sessions: list[SessionData] = []
        # sessions = await self._repository.get_sessions_by_status(status)

        if not sessions:
            return HealthCheckResult()

        keeper = self._health_keepers.get(status)
        if not keeper:
            log.trace("No health keeper for status {}", status)
            return HealthCheckResult()

        result = await keeper.handle_batch(sessions)

        log.info(
            "Checked {} sessions with status {}: {} healthy, {} unhealthy",
            len(sessions),
            status,
            len(result.healthy_sessions),
            len(result.unhealthy_sessions),
        )

        return result

    async def run_health_checks(self) -> dict[SessionStatus, HealthCheckResult]:
        """Run health checks for all monitored statuses.

        Returns:
            Dictionary mapping status to health check results
        """
        log.info("Running health checks for all monitored statuses")

        all_results: dict[SessionStatus, HealthCheckResult] = {}
        for status in self._health_keepers.keys():
            result = await self.check_sessions_by_status(status)
            if result.healthy_sessions or result.unhealthy_sessions:
                all_results[status] = result

        total_healthy = sum(len(r.healthy_sessions) for r in all_results.values())
        total_unhealthy = sum(len(r.unhealthy_sessions) for r in all_results.values())

        log.info(
            "Health check complete: {} healthy, {} unhealthy sessions",
            total_healthy,
            total_unhealthy,
        )

        return all_results
