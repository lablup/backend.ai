"""Handler for cleaning up containers of force-terminated sessions."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Sequence
from typing import TYPE_CHECKING, override

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.types import SessionId
from ai.backend.logging.structured import StructuredLogger, with_log_context
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.session.searchable_fields import SessionSearchableFields
from ai.backend.manager.models.session.searchers import SessionInfoSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.cleanup.base import CleanupHandler
from ai.backend.manager.sokovan.scheduler.hooks.registry import HookRegistry

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator
    from ai.backend.manager.views.sokovan.session import TerminatingSessionData

log = StructuredLogger(logging.getLogger(__name__))

MAX_NETWORK_RELEASE_ATTEMPTS = 5
# An RPC to an agent that died after it was connected never returns on its own.
DESTROY_TIMEOUT_SEC = 20.0
RELEASE_TIMEOUT_SEC = 5.0
# Bounds the DB queries and agent RPCs one cycle runs at once.
MAX_CONCURRENT_SESSIONS = 10


class CleanupForceTerminatedHandler(CleanupHandler):
    """Cleanup containers for force-terminated sessions.

    Force-terminated sessions skip the TERMINATING state and go directly to TERMINATED,
    bypassing the normal terminate handler that sends destroy RPCs to agents.
    This handler reads force-terminated session IDs from Valkey, fetches kernel/agent
    info from DB, and sends destroy RPCs to ensure containers are cleaned up.

    It also runs the TERMINATED hook, which the promotion pass skipped, to release the
    session network. A session whose destroy RPCs an agent refused stays queued and is sent
    them again (an agent ignores a repeated destroy); once every agent has accepted them,
    only a failed release is retried, at most ``MAX_NETWORK_RELEASE_ATTEMPTS`` times.
    """

    _terminator: SessionTerminator
    _repository: SchedulerRepository
    _valkey_schedule: ValkeyScheduleClient
    _hook_registry: HookRegistry

    def __init__(
        self,
        terminator: SessionTerminator,
        repository: SchedulerRepository,
        valkey_schedule: ValkeyScheduleClient,
        hook_registry: HookRegistry,
    ) -> None:
        self._terminator = terminator
        self._repository = repository
        self._valkey_schedule = valkey_schedule
        self._hook_registry = hook_registry

    @classmethod
    @override
    def name(cls) -> str:
        return "cleanup-force-terminated"

    @property
    @override
    def lock_id(self) -> LockID | None:
        """Exclusive, so overlapping cycles never count one release failure twice."""
        return LockID.LOCKID_SOKOVAN_CLEANUP_FORCE_TERMINATED

    @override
    async def fetch_session_ids(self) -> Sequence[SessionId]:
        return await self._valkey_schedule.get_force_terminated_sessions()

    @override
    async def execute(self, session_ids: Sequence[SessionId]) -> None:
        log.debug("force-terminated session cleanup processing", session_count=len(session_ids))

        release_attempts = await self._valkey_schedule.get_force_terminated_release_attempts()
        destroy_ids = [sid for sid in session_ids if sid not in release_attempts]
        flows: list[tuple[SessionId, Awaitable[bool]]] = []
        if destroy_ids:
            try:
                terminating_sessions, gone = await self._fetch_terminating(destroy_ids)
            except Exception:
                log.exception("fetching force-terminated sessions failed; kept queued")
            else:
                if gone:
                    try:
                        await self._valkey_schedule.remove_force_terminated_sessions(gone)
                    except Exception:
                        log.exception("dropping force-terminated ids with no session failed")
                flows.extend(
                    (s.session_id, self._destroy_then_release(s)) for s in terminating_sessions
                )
        flows.extend((sid, self._settle_one(sid)) for sid in session_ids if sid in release_attempts)

        # Each session runs to its end on its own, so a stuck agent delays only its own sessions.
        limit = asyncio.Semaphore(MAX_CONCURRENT_SESSIONS)
        finished = await asyncio.gather(*(self._finish(sid, flow, limit) for sid, flow in flows))
        log.debug(
            "force-terminated sessions cleaned up",
            success_count=sum(finished),
            failure_count=len(finished) - sum(finished),
        )

    async def _finish(
        self, session_id: SessionId, flow: Awaitable[bool], limit: asyncio.Semaphore
    ) -> bool:
        """Run one session's cleanup; drop it from the queue the moment it is done."""
        async with limit:
            if not await flow:
                return False
        with with_log_context(session_id=session_id):
            try:
                # Removed one by one: a cycle cut at its lock lifetime keeps what it finished.
                await self._valkey_schedule.remove_force_terminated_sessions([session_id])
            except Exception:
                log.exception("force-terminated session could not leave the queue; kept queued")
                return False
        return True

    async def _destroy_then_release(self, session_data: TerminatingSessionData) -> bool:
        if not await self._destroy_one(session_data):
            return False
        return await self._settle_one(session_data.session_id)

    async def _settle_one(self, session_id: SessionId) -> bool:
        with with_log_context(session_id=session_id):
            try:
                return await self._settle_release(session_id)
            except Exception:
                log.exception("force-terminated session cleanup failed; kept queued")
                return False

    async def _settle_release(self, session_id: SessionId) -> bool:
        """Release the network or count a failed attempt; True once the id may leave the queue."""
        try:
            if await self._release_network(session_id):
                return True
        except Exception:
            log.exception("force-terminated session network release failed")
        failures = await self._valkey_schedule.record_force_terminated_release_failure(session_id)
        if failures >= MAX_NETWORK_RELEASE_ATTEMPTS:
            log.warning(
                "giving up releasing the network of a force-terminated session",
                attempts=failures,
            )
            return True
        return False

    async def _fetch_terminating(
        self, session_ids: Sequence[SessionId]
    ) -> tuple[list[TerminatingSessionData], list[SessionId]]:
        """Return the sessions to destroy and the ids with no session data."""
        terminating_sessions = await self._repository.get_terminating_sessions_by_ids(
            list(session_ids)
        )
        found = {session_data.session_id for session_data in terminating_sessions}
        gone = [sid for sid in session_ids if sid not in found]
        if gone:
            log.debug(
                "no session data found for force-terminated sessions", session_count=len(gone)
            )
        return terminating_sessions, gone

    async def _destroy_one(self, session_data: TerminatingSessionData) -> bool:
        """True once every agent accepted the destroy RPCs; False keeps the session queued."""
        with with_log_context(session_id=session_data.session_id):
            try:
                async with asyncio.timeout(DESTROY_TIMEOUT_SEC):
                    confirmed = await self._terminator.terminate_sessions_for_handler([
                        session_data
                    ])
            except TimeoutError:
                log.warning(
                    "force-terminated session destroy timed out; kept queued",
                    timeout_sec=DESTROY_TIMEOUT_SEC,
                )
                return False
            except Exception:
                log.exception("force-terminated session cleanup failed")
                return False
            if session_data.session_id not in confirmed:
                # Releasing the network under a live container would only fail.
                log.warning("force-terminated session destroy refused by an agent; kept queued")
                return False
            return True

    async def _release_network(self, session_id: SessionId) -> bool:
        """Run the TERMINATED hook for one session to release its volatile network.

        False means the release failed and may be retried on the next cycle.
        """
        hook = self._hook_registry.get_hook(SessionStatus.TERMINATED)
        if hook is None:
            return True
        searcher = SessionInfoSearcher(
            pagination=NoPagination(),
            conditions=[
                SessionSearchableFields.own.id.filter.in_(
                    UUIDInMatchSpec(values=[session_id], negated=False)
                )
            ],
        )
        sessions = await self._repository.search_sessions_with_kernels_for_handler(searcher)
        if not sessions:
            # Nothing names the network any more; drop the id rather than retry forever.
            log.warning("no session data for force-terminated session; network not released")
            return True
        for session in sessions:
            try:
                async with asyncio.timeout(RELEASE_TIMEOUT_SEC):
                    await hook.execute(session)
            except Exception as e:
                log.warning("force-terminated session network release failed", error=repr(e))
                return False
        return True
