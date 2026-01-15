"""Handler for starting sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.types import AccessKey, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.repositories.scheduler.options import SessionConditions
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    ScheduledSessionData,
    SessionExecutionResult,
    SessionTransitionInfo,
)
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher

log = BraceStyleAdapter(logging.getLogger(__name__))


class StartSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for starting sessions that passed precondition checks.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with PREPARED status (provides HandlerSessionData)
    - Handler queries additional data (SessionDataForStart + ImageConfigData) via Repository
    - Handler starts kernels on agents via Launcher
    - Coordinator updates sessions to CREATING status
    """

    def __init__(
        self,
        launcher: SessionLauncher,
        repository: SchedulerRepository,
        event_producer: EventProducer,
    ) -> None:
        self._launcher = launcher
        self._repository = repository
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "start-sessions"

    @classmethod
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in PREPARED state."""
        return [SessionStatus.PREPARED]

    @classmethod
    def target_kernel_statuses(cls) -> list[KernelStatus]:
        """Include sessions where kernels are in PREPARED status."""
        return [KernelStatus.PREPARED]

    @classmethod
    def success_status(cls) -> Optional[SessionStatus]:
        """Sessions transition to CREATING on success."""
        return SessionStatus.CREATING

    @classmethod
    def failure_status(cls) -> Optional[SessionStatus]:
        """No failure status - sessions stay in PREPARED state."""
        return None

    @classmethod
    def stale_status(cls) -> Optional[SessionStatus]:
        """No stale status for this handler."""
        return None

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PREPARED sessions transitioning to CREATING."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    async def execute(
        self,
        scaling_group: str,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Start kernels on agents for PREPARED sessions.

        The coordinator provides SessionWithKernels data.
        This handler:
        1. Extracts session IDs from SessionWithKernels
        2. Queries Repository for additional data (SessionDataForStart + ImageConfigData)
        3. Starts kernels on agents via Launcher
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        # Extract session IDs from SessionWithKernels
        session_ids = [s.session_info.identity.id for s in sessions]

        # Query Repository for additional data needed by Launcher
        # Use search_sessions_with_kernels_and_user to get user info for session start
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[SessionConditions.by_ids(session_ids)],
        )
        sessions_data = await self._repository.search_sessions_with_kernels_and_user(querier)

        # Start kernels on agents via Launcher
        # Note: RecorderContext is handled inside Launcher
        await self._launcher.start_sessions_for_handler(
            sessions_data.sessions,
            sessions_data.image_configs,
        )

        # Mark all sessions as success for status transition
        for session in sessions:
            session_info = session.session_info
            result.successes.append(
                SessionTransitionInfo(
                    session_id=session_info.identity.id,
                    from_status=session_info.lifecycle.status,
                )
            )
            result.scheduled_data.append(
                ScheduledSessionData(
                    session_id=session_info.identity.id,
                    creation_id=session_info.identity.creation_id,
                    access_key=AccessKey(session_info.metadata.access_key),
                    reason="triggered-by-scheduler",
                )
            )

        return result

    async def post_process(self, result: SessionExecutionResult) -> None:
        """Log the number of started sessions and broadcast events."""
        log.info("Started {} sessions", len(result.scheduled_data))

        events: list[AbstractBroadcastEvent] = [
            SchedulingBroadcastEvent(
                session_id=event_data.session_id,
                creation_id=event_data.creation_id,
                status_transition=str(SessionStatus.CREATING),
                reason=event_data.reason,
            )
            for event_data in result.scheduled_data
        ]
        await self._event_producer.broadcast_events_batch(events)
