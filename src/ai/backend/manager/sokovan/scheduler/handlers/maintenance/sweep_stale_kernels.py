"""Handler for sweeping kernels with stale presence status."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
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


class SweepStaleKernelsHandler(SchedulerHandler):
    """Handler for sweeping kernels with stale presence status.

    This handler checks kernel presence status in Redis and terminates
    kernels that are STALE (no heartbeat from agent for too long).
    Before termination, it confirms with the agent that the kernel
    is truly gone.
    """

    def __init__(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        scheduler: Scheduler,
        repository: SchedulerRepository,
    ) -> None:
        self._valkey_schedule_client = valkey_schedule_client
        self._scheduler = scheduler
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-stale-kernels"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Sweep kernels with stale presence status."""
        return await self._scheduler.sweep_stale_kernels()

    async def post_process(self, result: ScheduleResult) -> None:
        """Trigger CHECK_RUNNING_SESSION_TERMINATION and invalidate cache if kernels were terminated."""
        log.info("Swept {} stale kernels", len(result.scheduled_sessions))

        # Trigger CHECK_RUNNING_SESSION_TERMINATION to check if sessions need termination
        await self._valkey_schedule_client.mark_schedule_needed(
            ScheduleType.CHECK_RUNNING_SESSION_TERMINATION
        )

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))


class SweepStaleKernelsLifecycleHandler(SessionLifecycleHandler):
    """Handler for sweeping kernels with stale presence status.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with kernels that may be stale
    - Handler checks kernel presence in Redis and terminates stale ones
    - Before termination, confirms with agent that kernel is truly gone
    """

    def __init__(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        scheduler: Scheduler,
        repository: SchedulerRepository,
    ) -> None:
        self._valkey_schedule_client = valkey_schedule_client
        self._scheduler = scheduler
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-stale-kernels"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions with running kernels that may be stale."""
        return [SessionStatus.RUNNING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Any kernel status for stale check."""
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
        """Stale kernels lead to TERMINATING status."""
        return SessionStatus.TERMINATING

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[HandlerSessionData],
    ) -> SessionExecutionResult:
        """Sweep kernels with stale presence status.

        Delegates to Scheduler's sweep method which handles:
        - Checking kernel presence status in Redis
        - Confirming with agent that kernels are truly gone
        - Terminating stale kernels
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Delegate to existing Scheduler method
        schedule_result = await self._scheduler.sweep_stale_kernels()

        # Mark swept sessions as stale for status transition
        for event_data in schedule_result.scheduled_sessions:
            result.stales.append(event_data.session_id)
            result.scheduled_data.append(event_data)

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Trigger CHECK_RUNNING_SESSION_TERMINATION and invalidate cache."""
        log.info("Swept {} stale kernels", len(result.stales))

        # Trigger CHECK_RUNNING_SESSION_TERMINATION to check if sessions need termination
        await self._valkey_schedule_client.mark_schedule_needed(
            ScheduleType.CHECK_RUNNING_SESSION_TERMINATION
        )

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_data
        }
        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))
