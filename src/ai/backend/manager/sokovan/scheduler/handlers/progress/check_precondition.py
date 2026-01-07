"""Handler for checking session preconditions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.handlers.base import (
    SchedulerHandler,
    SessionLifecycleHandler,
)
from ai.backend.manager.sokovan.scheduler.results import (
    HandlerSessionData,
    ScheduledSessionData,
    ScheduleResult,
    SessionExecutionResult,
)
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher

log = BraceStyleAdapter(logging.getLogger(__name__))


class CheckPreconditionHandler(SchedulerHandler):
    """Handler for checking session preconditions."""

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
        return "check-precondition"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PREPARING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(self) -> ScheduleResult:
        """Check preconditions for scheduled sessions."""
        return await self._scheduler.check_preconditions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request session start if preconditions are met."""
        # Request next phase first
        log.info("Checked preconditions for {} sessions", len(result.scheduled_sessions))
        await self._scheduling_controller.mark_scheduling_needed(ScheduleType.START)

        # Broadcast batch event for sessions that passed precondition check
        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.PREPARING),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_sessions
        ]
        await self._event_producer.broadcast_events_batch(events)


class CheckPreconditionLifecycleHandler(SessionLifecycleHandler):
    """Handler for checking session preconditions and triggering image pulling.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with SCHEDULED status (provides HandlerSessionData)
    - Handler queries additional data (SessionDataForPull + ImageConfigData) via Repository
    - Handler triggers image pulling on agents via Launcher
    - Coordinator updates sessions to PREPARING status
    """

    def __init__(
        self,
        launcher: SessionLauncher,
        repository: SchedulerRepository,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
    ) -> None:
        self._launcher = launcher
        self._repository = repository
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-precondition"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in SCHEDULED state."""
        return [SessionStatus.SCHEDULED]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Include sessions where kernels are in SCHEDULED status."""
        return [KernelStatus.SCHEDULED]

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """Sessions transition to PREPARING on success."""
        return SessionStatus.PREPARING

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status - sessions stay in SCHEDULED state."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """No stale status for this handler."""
        return None

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting SCHEDULED sessions transitioning to PREPARING."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[HandlerSessionData],
    ) -> SessionExecutionResult:
        """Trigger image pulling for SCHEDULED sessions.

        The coordinator provides basic session info (HandlerSessionData).
        This handler:
        1. Extracts session IDs from HandlerSessionData
        2. Queries Repository for additional data (SessionDataForPull + ImageConfigData)
        3. Triggers image pulling via Launcher
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from HandlerSessionData
        session_ids = [s.session_id for s in sessions]

        # Query Repository for additional data needed by Launcher
        sessions_for_pull_data = await self._repository.get_sessions_for_pull_by_ids(session_ids)

        # Trigger image pulling via Launcher with the full data
        await self._launcher.trigger_image_pulling(
            sessions_for_pull_data.sessions,
            sessions_for_pull_data.image_configs,
        )

        # Mark all sessions as success for status transition
        for session in sessions:
            result.successes.append(session.session_id)
            result.scheduled_data.append(
                ScheduledSessionData(
                    session_id=session.session_id,
                    creation_id=session.creation_id,
                    access_key=session.access_key,
                    reason="passed-preconditions",
                )
            )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Request session start and broadcast events."""
        log.info("Checked preconditions for {} sessions", len(result.scheduled_data))
        await self._scheduling_controller.mark_scheduling_needed(ScheduleType.START)

        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.PREPARING),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_data
        ]
        await self._event_producer.broadcast_events_batch(events)
