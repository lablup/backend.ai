"""Handler for retrying creating sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.common.events.dispatcher import EventProducer
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
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher

log = BraceStyleAdapter(logging.getLogger(__name__))

# Time thresholds for health checks
CREATING_CHECK_THRESHOLD = 600.0  # 10 minutes


class RetryCreatingHandler(SchedulerHandler):
    """Handler for retrying CREATING sessions that appear stuck."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
    ) -> None:
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "retry-creating"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting CREATING sessions (retry)."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(self) -> ScheduleResult:
        """Check and retry stuck CREATING sessions."""
        log.debug("Checking for stuck CREATING sessions to retry")

        # Call scheduler method to handle retry logic
        return await self._scheduler.retry_creating_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request session start if sessions were retried."""
        log.info("Retried {} stuck CREATING sessions", len(result.scheduled_sessions))


class RetryCreatingLifecycleHandler(SessionLifecycleHandler):
    """Handler for retrying CREATING sessions that appear stuck.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with CREATING status
    - Handler checks if sessions are truly stuck and retries them
    - Sessions exceeding max retries are marked as stale (TERMINATING)
    """

    def __init__(
        self,
        launcher: SessionLauncher,
        repository: SchedulerRepository,
    ) -> None:
        self._launcher = launcher
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "retry-creating"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in CREATING state."""
        return [SessionStatus.CREATING]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Any kernel status - we check stuck sessions regardless."""
        return []

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """No status change on retry - sessions stay in CREATING."""
        return None

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status for retry handler."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """Sessions exceeding max retries transition to TERMINATING."""
        return SessionStatus.TERMINATING

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting CREATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(
        self,
        sessions: Sequence[HandlerSessionData],
        scaling_group: str,
    ) -> SessionExecutionResult:
        """Check and retry stuck CREATING sessions.

        Delegates to Launcher's retry method which handles:
        - Filtering truly stuck sessions
        - Checking with agents if sessions are actively creating
        - Updating retry counts
        - Re-triggering session creation for sessions that should retry
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Delegate to existing Launcher method which handles all the logic
        await self._launcher.retry_creating_sessions()

        # Don't mark any status changes - the Launcher handles retry counts
        # and moves sessions to TERMINATING if max retries exceeded

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Log retry results."""
        log.info("Completed retry check for CREATING sessions")
