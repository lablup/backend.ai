"""Handler for cleaning up containers of force-terminated sessions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.handlers.cleanup.base import CleanupHandler

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator

log = BraceStyleAdapter(logging.getLogger(__name__))


class CleanupForceTerminatedHandler(CleanupHandler):
    """Cleanup containers for force-terminated sessions.

    Force-terminated sessions skip the TERMINATING state and go directly to TERMINATED,
    bypassing the normal terminate handler that sends destroy RPCs to agents.
    This handler reads force-terminated session IDs from Valkey, fetches kernel/agent
    info from DB, and sends destroy RPCs to ensure containers are cleaned up.
    """

    def __init__(
        self,
        terminator: SessionTerminator,
        repository: SchedulerRepository,
        valkey_schedule: ValkeyScheduleClient,
    ) -> None:
        self._terminator = terminator
        self._repository = repository
        self._valkey_schedule = valkey_schedule

    @classmethod
    def name(cls) -> str:
        return "cleanup-force-terminated"

    async def execute(self) -> None:
        session_ids = await self._valkey_schedule.pop_force_terminated_sessions()
        if not session_ids:
            return

        log.info("Processing {} force-terminated sessions for container cleanup", len(session_ids))

        terminating_sessions = await self._repository.get_terminating_sessions_by_ids(session_ids)
        if not terminating_sessions:
            log.warning(
                "No session data found for force-terminated sessions: {}",
                session_ids,
            )
            return

        terminating_session_ids = [s.session_id for s in terminating_sessions]
        try:
            with RecorderContext[SessionId].scope(
                "cleanup_force_terminated", entity_ids=terminating_session_ids
            ):
                await self._terminator.terminate_sessions_for_handler(terminating_sessions)
        except Exception:
            log.exception(
                "Error sending cleanup RPCs for force-terminated sessions: {}",
                terminating_session_ids,
            )
