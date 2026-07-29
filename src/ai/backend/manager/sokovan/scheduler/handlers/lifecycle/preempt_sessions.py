"""Handler for branching preemption victims (PREEMPTED sessions)."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, override

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import PreemptionMode
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
    from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__name__))

_PREEMPTION_REASON = "PREEMPTED_BY_SCHEDULER"


class PreemptSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler that routes confirmed preemption victims (BEP-1055 eviction).

    A victim enters PREEMPTED via ``SchedulingController.mark_sessions_status``.
    This handler only picks the branch the resource group's ``PreemptionMode``
    asks for; the follow-up work belongs to the target status' own handler, and
    the branches differ in what they write:

    - ``terminate`` -> TERMINATING for the session and its kernels alike, under
      the preemption reason; finished by the termination path.
    - ``reschedule`` -> RESCHEDULING for the session only. The kernels stand
      until :class:`RescheduleSessionsLifecycleHandler` tears them down on a
      later tick and re-enqueues the session.

    This handler is self-driven: ``status_transitions()`` declares no transition
    because the target depends on the per-resource-group mode, which a static
    transition table cannot express. It writes the status itself and returns an
    empty result.
    """

    _repository: SchedulerRepository
    _scheduling_controller: SchedulingController

    def __init__(
        self,
        repository: SchedulerRepository,
        scheduling_controller: SchedulingController,
    ) -> None:
        self._repository = repository
        self._scheduling_controller = scheduling_controller

    @classmethod
    @override
    def name(cls) -> str:
        return "preempt-sessions"

    @classmethod
    @override
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in PREEMPTED state."""
        return [SessionStatus.PREEMPTED]

    @classmethod
    @override
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """No kernel filtering — the branch depends on the mode, not on kernels."""
        return None

    @classmethod
    @override
    def status_transitions(cls) -> StatusTransitions:
        """Self-driven handler — no coordinator transitions (see class docstring)."""
        return StatusTransitions()

    @property
    @override
    def lock_id(self) -> LockID | None:
        """Lock for operations targeting PREEMPTED sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREEMPTED

    @override
    async def execute(
        self,
        resource_group_id: ResourceGroupID,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        result = SessionExecutionResult()
        if not sessions:
            return result

        session_ids = [session.session_info.identity.id for session in sessions]
        mode = await self._repository.get_resource_group_preemption_mode(resource_group_id)
        if mode == PreemptionMode.RESCHEDULE:
            marked = await self._scheduling_controller.mark_sessions_status(
                session_ids,
                SessionStatus.RESCHEDULING,
                reason=_PREEMPTION_REASON,
            )
            await self._scheduling_controller.mark_scheduling_needed([ScheduleType.RESCHEDULING])
            log.info("Sent {} preemption victims to rescheduling", len(marked))
        else:
            await self._scheduling_controller.mark_sessions_for_termination(
                session_ids,
                reason=_PREEMPTION_REASON,
                message="preempt_terminate success",
            )
            log.info("Sent {} preemption victims to termination", len(session_ids))
        return result
