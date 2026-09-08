"""Handler for starting sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from enum import StrEnum
from typing import TYPE_CHECKING, Final, override

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


class _StartDisposition(StrEnum):
    """What this handler should do with one session it has been handed."""

    #: Every kernel is where a start begins from. Start it.
    START = "start"
    #: No kernel of this session can be holding a container, and they are not all in a state a
    #: start begins from. Nothing is running, so the whole session goes back in the queue: the
    #: REPLACE transition resets every kernel to PENDING, unbinds them, and re-schedules.
    REQUEUE = "requeue"
    #: A kernel may hold a container -- it is in a status that has one, has been through one, or
    #: still names one. Not this handler's to judge: the progress and termination passes own it.
    NOT_OURS = "not_ours"


#: Kernel statuses a session can legitimately be STARTED from. Anything outside this set means
#: the session is not simply waiting to be started.
_STARTABLE_FROM: Final = frozenset({KernelStatus.PREPARED})

#: Kernel statuses that mean no container of that kernel can exist yet -- nothing has been asked
#: of an agent for it. A session all of whose kernels are in here has nothing running to lose.
_BEFORE_ANY_CONTAINER: Final = frozenset({
    KernelStatus.PENDING,
    KernelStatus.RESERVED,
    KernelStatus.SCHEDULED,
    KernelStatus.PREPARING,
    KernelStatus.BUILDING,
    KernelStatus.PREPARED,
})


def _disposition_of(session: SessionWithKernels) -> _StartDisposition:
    """Which of the three things a session handed to this handler is.

    The handler's kernel filter is coarse -- the repository returns a session if ANY of its
    kernels matches -- so what arrives here is not only sessions waiting to be started. Two other
    shapes arrive with them, and telling them apart by what is SAFE rather than by what is
    expected is what keeps this from acting on a session it does not own:

    - A session whose kernels were reset to PENDING without its own status following. Its move to
      PENDING and its kernels' reset are two transactions and the kernels go first, so a manager
      dying between them leaves exactly this. Nothing selects it otherwise: the scheduler wants
      PENDING SESSIONS. It is finished here.
    - A session whose kernels disagree. If none of them can hold a container, the same answer
      applies for the same reason: nothing is running, so the whole thing goes back in the queue
      and is scheduled cleanly. If any of them can, this handler must not touch it -- rebuilding
      the kernels that still have an agent would leave a session half old and half new.

    The container test is deliberately the strong one: a status that has a container, a status
    that has been through one, or a kernel that still names one. A stale container id under a
    PENDING kernel is precisely the case where "it looks unbound" is wrong.
    """
    kernels = session.kernel_infos
    if not kernels:
        # Nothing to start and nothing that could be running. Requeue rather than report a
        # session with no kernels as started, which is what a start of it would amount to.
        return _StartDisposition.REQUEUE
    if all(k.lifecycle.status in _STARTABLE_FROM for k in kernels):
        return _StartDisposition.START
    if any(
        k.resource.container_id is not None or k.lifecycle.status not in _BEFORE_ANY_CONTAINER
        for k in kernels
    ):
        return _StartDisposition.NOT_OURS
    return _StartDisposition.REQUEUE


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

        The filter is coarse: the repository returns a session if ANY of its kernels matches, so
        `_disposition_of` decides what has actually been handed over -- see there.
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

        # What each session actually is, before anything is done to it. See `_disposition_of`.
        startable: list[SessionWithKernels] = []
        for session in sessions:
            info = session.session_info
            match _disposition_of(session):
                case _StartDisposition.START:
                    startable.append(session)
                case _StartDisposition.REQUEUE:
                    log.warning(
                        "session {} cannot be started as it stands and nothing of it is running;"
                        " putting it back in the queue",
                        info.identity.id,
                    )
                    result.failures.append(
                        SessionTransitionInfo(
                            session_id=info.identity.id,
                            from_status=info.lifecycle.status,
                            reason="kernels are not in a state this session can be started from",
                            creation_id=info.identity.creation_id,
                            access_key=AccessKey(info.metadata.access_key),
                            disposition=FailureDisposition.REPLACE,
                        )
                    )
                case _StartDisposition.NOT_OURS:
                    log.warning(
                        "session {} has a kernel that may hold a container; leaving it to the"
                        " pass that owns that",
                        info.identity.id,
                    )
                    result.skipped.append(
                        SessionTransitionInfo(
                            session_id=info.identity.id,
                            from_status=info.lifecycle.status,
                            reason="a kernel may hold a container",
                            creation_id=info.identity.creation_id,
                            access_key=AccessKey(info.metadata.access_key),
                        )
                    )

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
