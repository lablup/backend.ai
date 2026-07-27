"""Handler for advancing RESERVED sessions whose reservations became satisfiable."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import (
    SessionStatus,
    StatusTransitions,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
)
from ai.backend.manager.views.sokovan.lifecycle import SessionWithKernels

log = BraceStyleAdapter(logging.getLogger(__name__))

_RELEASE_REASON = "RESERVATION_RELEASED"


class ReleaseReservedSessionsLifecycleHandler(SessionLifecycleHandler):
    """Advance RESERVED sessions once their victims' resources are freed.

    A session enters RESERVED when its preemption plan reserves resources up
    front (BEP-1055). Each cycle the repository judges which reservations are
    admittable (first reserved, first released, within each agent's restored
    capacity); those sessions succeed into SCHEDULED — the coordinator writes
    the transition and the schedule-marking post-processor triggers the
    precondition check — while the rest are skipped and stay RESERVED. The
    hold itself was established at reservation time, so no re-reservation
    happens.
    """

    _repository: SchedulerRepository

    def __init__(self, repository: SchedulerRepository) -> None:
        self._repository = repository

    @classmethod
    @override
    def name(cls) -> str:
        return "release-reserved-sessions"

    @classmethod
    @override
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions holding a reservation."""
        return [SessionStatus.RESERVED]

    @classmethod
    @override
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """Kernels holding the reservation."""
        return [KernelStatus.RESERVED]

    @classmethod
    @override
    def status_transitions(cls) -> StatusTransitions:
        """Kernel admission happens in the repository; the session advances
        via the CHECK_RESERVED_PROGRESS promotion once no kernel stays
        RESERVED."""
        return StatusTransitions()

    @property
    @override
    def lock_id(self) -> LockID | None:
        """Lock for operations targeting RESERVED sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_RESERVED

    @override
    async def execute(
        self,
        resource_group_id: ResourceGroupID,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        result = SessionExecutionResult()
        if not sessions:
            return result

        # Admission (the prereserved -> reserved move) happens atomically in
        # the repository, first reserved first; only the admitted sessions
        # transition here.
        session_ids = [session.session_info.identity.id for session in sessions]
        admitted = await self._repository.admit_prereserved_kernels(session_ids)
        if admitted:
            log.info("Admitted {} prereserved kernels", len(admitted))

        return result
