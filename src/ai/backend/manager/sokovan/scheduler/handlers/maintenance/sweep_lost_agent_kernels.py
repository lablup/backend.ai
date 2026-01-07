"""Handler for sweeping kernels with lost agents."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import (
    SchedulerHandler,
    SessionLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerSessionData,
    ScheduleResult,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

log = BraceStyleAdapter(logging.getLogger(__name__))


class SweepLostAgentKernelsHandler(SchedulerHandler):
    """Handler for sweeping kernels with lost or missing agents."""

    def __init__(
        self,
        scheduler: Scheduler,
        repository: SchedulerRepository,
    ) -> None:
        self._scheduler = scheduler
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-lost-agent-kernels"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Sweep kernels with lost or missing agents."""
        return await self._scheduler.sweep_lost_agent_kernels()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of swept kernels and invalidate cache."""
        log.info("Swept {} sessions with lost agent kernels", len(result.scheduled_sessions))
        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        await self._repository.invalidate_kernel_related_cache(list(affected_keys))
        log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))


class SweepLostAgentKernelsLifecycleHandler(SessionLifecycleHandler):
    """Handler for sweeping kernels with lost or missing agents.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with kernels whose agents are lost
    - Handler determines which sessions should be swept
    - Sessions with lost agent kernels are moved to TERMINATING status
    """

    def __init__(
        self,
        scheduler: Scheduler,
        repository: SchedulerRepository,
    ) -> None:
        self._scheduler = scheduler
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-lost-agent-kernels"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions with running kernels that may have lost agents."""
        return [SessionStatus.RUNNING, SessionStatus.CREATING, SessionStatus.PREPARING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Any kernel status for lost agent check."""
        return []

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """No success status for sweep handler."""
        return None

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status for sweep handler."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """Sessions with lost agents transition to TERMINATING."""
        return SessionStatus.TERMINATING

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(
        self,
        sessions: Sequence[HandlerSessionData],
        scaling_group: str,
    ) -> SessionExecutionResult:
        """Sweep kernels with lost or missing agents.

        Delegates to Scheduler's sweep method which handles:
        - Checking agent presence and status
        - Determining which kernels belong to lost agents
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Delegate to existing Scheduler method
        schedule_result = await self._scheduler.sweep_lost_agent_kernels()

        # Mark swept sessions as stale for status transition
        for event_data in schedule_result.scheduled_sessions:
            result.stales.append(event_data.session_id)
            result.scheduled_data.append(event_data)

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Log the number of swept kernels and invalidate cache."""
        log.info("Swept {} sessions with lost agent kernels", len(result.stales))
        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_data
        }
        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))
