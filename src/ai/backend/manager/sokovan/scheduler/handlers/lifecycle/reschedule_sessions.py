"""Handler for putting rescheduling sessions back in the queue."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, override

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import SessionExecutionResult
from ai.backend.manager.sokovan.scheduler.types import ScheduleType
from ai.backend.manager.views.sokovan.lifecycle import SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.terminator.terminator import SessionTerminator
    from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__name__))

_RESCHEDULE_REASON = "RESCHEDULED"


class RescheduleSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler that returns RESCHEDULING sessions to the queue.

    A session enters RESCHEDULING when something decides it should run again
    from scratch — today a preemption victim in ``reschedule`` mode. This handler
    tears its kernels down and, once every kernel is gone, re-enqueues the same
    session as PENDING with its id, config and priorities intact.

    It runs across ticks: while kernels remain, it re-sends the destruction
    request (as the termination path does) and the session stays RESCHEDULING.

    This handler is self-driven: ``status_transitions()`` declares no transition
    because a session only leaves RESCHEDULING once its kernels are terminal,
    which a static transition table cannot express.
    """

    _terminator: SessionTerminator
    _repository: SchedulerRepository
    _scheduling_controller: SchedulingController

    def __init__(
        self,
        terminator: SessionTerminator,
        repository: SchedulerRepository,
        scheduling_controller: SchedulingController,
    ) -> None:
        self._terminator = terminator
        self._repository = repository
        self._scheduling_controller = scheduling_controller

    @classmethod
    @override
    def name(cls) -> str:
        return "reschedule-sessions"

    @classmethod
    @override
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in RESCHEDULING state."""
        return [SessionStatus.RESCHEDULING]

    @classmethod
    @override
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """No kernel filtering — sessions awaiting teardown and sessions ready to
        be re-enqueued are both handled here."""
        return None

    @classmethod
    @override
    def status_transitions(cls) -> StatusTransitions:
        """Self-driven handler — no coordinator transitions (see class docstring)."""
        return StatusTransitions()

    @property
    @override
    def lock_id(self) -> LockID | None:
        """Lock for operations targeting RESCHEDULING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_RESCHEDULING

    @override
    async def execute(
        self,
        resource_group_id: ResourceGroupID,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        result = SessionExecutionResult()
        if not sessions:
            return result

        awaiting_teardown: list[SessionId] = []
        ready_to_requeue: list[SessionId] = []
        for session in sessions:
            session_id = session.session_info.identity.id
            if all(
                kernel.lifecycle.status in KernelStatus.terminal_statuses()
                for kernel in session.kernel_infos
            ):
                ready_to_requeue.append(session_id)
            else:
                awaiting_teardown.append(session_id)

        if awaiting_teardown:
            await self._tear_down(awaiting_teardown)
        if ready_to_requeue:
            await self._requeue(ready_to_requeue)
        return result

    async def _tear_down(self, session_ids: list[SessionId]) -> None:
        """Ask the agents to destroy the kernels still standing.

        The sessions stay RESCHEDULING and this pass' own cycle picks them up
        again; re-marking it here would re-arm the pass every tick and keep
        re-sending the destruction request while the agents work.
        """
        terminating_sessions = await self._repository.get_terminating_sessions_by_ids(session_ids)
        if terminating_sessions:
            await self._terminator.terminate_sessions_for_handler(terminating_sessions)
        log.info("Tearing down kernels of {} rescheduling sessions", len(session_ids))

    async def _requeue(self, session_ids: list[SessionId]) -> None:
        """Put the sessions back in the queue now that their kernels are gone:
        the kernels drop their placement first, then the sessions become PENDING
        so the scheduling pass can pick them up."""
        await self._repository.reset_kernels_to_pending_for_sessions(
            session_ids, _RESCHEDULE_REASON
        )
        requeued = await self._scheduling_controller.mark_sessions_status(
            session_ids,
            SessionStatus.PENDING,
            reason=_RESCHEDULE_REASON,
        )
        await self._scheduling_controller.mark_scheduling_needed([ScheduleType.SCHEDULE])
        log.info("Requeued {} rescheduling sessions to PENDING", len(requeued))
