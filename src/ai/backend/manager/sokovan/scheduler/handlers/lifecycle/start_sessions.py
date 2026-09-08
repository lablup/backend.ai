"""Handler for starting sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions, TransitionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.session.conditions import SessionConditions
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    FailureDisposition,
    SessionExecutionResult,
    SessionTransitionInfo,
)
from ai.backend.manager.views.sokovan.lifecycle import SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher

log = BraceStyleAdapter(logging.getLogger(__name__))


class StartSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for starting sessions that passed precondition checks.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with PREPARED status (provides HandlerSessionData)
    - Handler queries additional data (SessionDataForStart + ImageConfigData) via Repository
    - Handler starts kernels on agents via Launcher
    - Coordinator updates sessions to CREATING status and broadcasts events
    """

    def __init__(
        self,
        launcher: SessionLauncher,
        repository: SchedulerRepository,
    ) -> None:
        self._launcher = launcher
        self._repository = repository

    @classmethod
    @override
    def name(cls) -> str:
        """Get the name of the handler."""
        return "start-sessions"

    @classmethod
    @override
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in PREPARED state."""
        return [SessionStatus.PREPARED]

    @classmethod
    @override
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """Sessions with a kernel in PREPARED status -- or in PENDING.

        PENDING is here for one state, and this handler is the only way out of it. The session's
        move to PENDING and its kernels' reset are two transactions: the kernels go first, so a
        manager that dies between them leaves a PREPARED session whose kernels are already PENDING
        and unbound. Without PENDING in this filter nothing selects that session at all -- the
        scheduler wants PENDING SESSIONS -- and it waits for a person.

        The filter is coarse: the repository returns a session if ANY of its kernels matches. So
        `execute` decides what it has actually been given, and only a session whose kernels are
        ALL PENDING and unbound is completed; a mixture is skipped rather than started. Widening
        this without that check would hand the launcher sessions whose kernels are half in other
        states, and it would dispatch to the ones that still have an agent.
        """
        return [KernelStatus.PREPARED, KernelStatus.PENDING]

    @classmethod
    @override
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for start sessions handler (BEP-1030).

        - success: Session/kernel → CREATING
        - need_retry: None (stays PREPARED)
        - expired: Session/kernel → PENDING (re-scheduling after timeout —
          a different agent or a later slot may succeed)
        - give_up: Session/kernel → TERMINATING (retry budget exhausted —
          repeatedly failing to start a kernel signals a persistent
          problem with the kernel spec or environment; we surface the
          failure rather than rescheduling indefinitely)
        """
        return StatusTransitions(
            success=TransitionStatus(
                session=SessionStatus.CREATING,
                kernel=KernelStatus.CREATING,
            ),
            need_retry=None,
            expired=TransitionStatus(
                session=SessionStatus.PENDING,
                kernel=KernelStatus.PENDING,
            ),
            give_up=TransitionStatus(
                session=SessionStatus.TERMINATING,
                kernel=KernelStatus.TERMINATING,
            ),
        )

    @property
    @override
    def lock_id(self) -> LockID | None:
        """Lock for operations targeting PREPARED sessions transitioning to CREATING."""
        return LockID.LOCKID_SOKOVAN_TARGET_CREATING

    @override
    async def execute(
        self,
        _resource_group_id: ResourceGroupID,
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

        # Sessions whose kernels have ALREADY been reset are not started; they are finished.
        # See `target_kernel_statuses` for how they arise. They are reported straight to the
        # coordinator as a placement to make again, and the launcher never sees them -- asking it
        # to start a session with no agent on any kernel would work, but only by accident.
        startable: list[SessionWithKernels] = []
        for session in sessions:
            kernels = session.kernel_infos
            if kernels and all(
                k.lifecycle.status == KernelStatus.PENDING and k.resource.agent is None
                for k in kernels
            ):
                info = session.session_info
                log.warning(
                    "session {} has been reset to PENDING kernels without its own status"
                    " following; completing that transition",
                    info.identity.id,
                )
                result.failures.append(
                    SessionTransitionInfo(
                        session_id=info.identity.id,
                        from_status=info.lifecycle.status,
                        reason="kernels were reset without the session following",
                        creation_id=info.identity.creation_id,
                        access_key=AccessKey(info.metadata.access_key),
                        disposition=FailureDisposition.REPLACE,
                    )
                )
                continue
            if any(k.lifecycle.status == KernelStatus.PENDING for k in kernels):
                # A mixture. Not the state above and not one to start either: dispatching would
                # ask agents to create some of the kernels of a session whose others are in
                # another state entirely. Left for the pass that owns whatever it actually is.
                log.warning(
                    "session {} has some kernels PENDING and some not; not starting it",
                    session.session_info.identity.id,
                )
                result.skipped.append(
                    SessionTransitionInfo(
                        session_id=session.session_info.identity.id,
                        from_status=session.session_info.lifecycle.status,
                        reason="kernel statuses disagree",
                        creation_id=session.session_info.identity.creation_id,
                        access_key=AccessKey(session.session_info.metadata.access_key),
                    )
                )
                continue
            startable.append(session)

        sessions = startable
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
        failed = await self._launcher.start_sessions_for_handler(
            sessions_data.sessions,
            sessions_data.image_configs,
        )

        # A session that did not start is not a success, and the two ways of not starting want
        # opposite things. Nothing asked of any agent -- a node whose data plane refuses the
        # session -- is a placement to give up and make again elsewhere; that node is now recorded
        # against the session, so the next one avoids it. Kernels already requested cannot be
        # placed a second time and are torn down. Both were reported as started, which left the
        # session in CREATING on a node it was not running on until something timed it out.
        for session in sessions:
            session_info = session.session_info
            failure = failed.get(session_info.identity.id)
            transition = SessionTransitionInfo(
                session_id=session_info.identity.id,
                from_status=session_info.lifecycle.status,
                reason=failure.reason if failure is not None else "triggered-by-scheduler",
                creation_id=session_info.identity.creation_id,
                access_key=AccessKey(session_info.metadata.access_key),
                # Carried through, because the retry counters cannot work it out: a placement that
                # will fail identically every time is given up now and made again elsewhere, and
                # a session whose kernels were already requested somewhere is torn down rather
                # than placed a second time.
                disposition=failure.disposition if failure is not None else None,
            )
            if failure is not None:
                result.failures.append(transition)
            else:
                result.successes.append(transition)

        return result
