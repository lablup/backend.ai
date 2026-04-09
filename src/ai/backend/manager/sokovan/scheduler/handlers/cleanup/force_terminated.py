"""Handler for cleaning up containers of force-terminated sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
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

    Only successfully cleaned-up session IDs are removed from Valkey; failed ones
    remain for retry on the next cycle.
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

    async def fetch_session_ids(self) -> Sequence[SessionId]:
        return await self._valkey_schedule.get_force_terminated_sessions()

    async def execute(self, session_ids: Sequence[SessionId]) -> None:
        log.info("Processing {} force-terminated sessions for container cleanup", len(session_ids))

        terminating_sessions = await self._repository.get_terminating_sessions_by_ids(
            list(session_ids)
        )
        if not terminating_sessions:
            log.warning(
                "No session data found for force-terminated sessions: {}",
                session_ids,
            )
            # Sessions no longer exist in DB — remove from Valkey to avoid infinite retry
            await self._valkey_schedule.remove_force_terminated_sessions(session_ids)
            return

        succeeded_ids: list[SessionId] = []
        for session_data in terminating_sessions:
            try:
                await self._terminator.terminate_sessions_for_handler([session_data])
                succeeded_ids.append(session_data.session_id)
            except Exception:
                log.exception(
                    "Failed to send cleanup RPC for force-terminated session {}",
                    session_data.session_id,
                )

        if succeeded_ids:
            await self._valkey_schedule.remove_force_terminated_sessions(succeeded_ids)
            log.info(
                "Cleaned up {} force-terminated sessions ({} failed)",
                len(succeeded_ids),
                len(terminating_sessions) - len(succeeded_ids),
            )
