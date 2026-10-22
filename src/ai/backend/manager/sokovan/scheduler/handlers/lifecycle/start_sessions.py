"""Handler for starting sessions."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import AccessKey
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus, StatusTransitions, TransitionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.session.searchable_fields import SessionSearchableFields
from ai.backend.manager.models.session.searchers import SessionSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.handlers.base import SessionLifecycleHandler
from ai.backend.manager.sokovan.scheduler.results import (
    SessionExecutionResult,
    SessionTransitionInfo,
)
from ai.backend.manager.views.sokovan.lifecycle import SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.launcher.launcher import SessionLauncher

log = StructuredLogger(logging.getLogger(__name__))


class StartSessionsLifecycleHandler(SessionLifecycleHandler):
    """Handler for starting sessions that passed precondition checks.

    Following the DeploymentCoordinator pattern:
    - Coordinator queries sessions with PREPARED status (provides HandlerSessionData)
    - Handler claims the sessions by moving them and their kernels to CREATING
    - Handler queries additional data (SessionDataForStart + ImageConfigData) via Repository
    - Handler starts kernels on agents via Launcher
    - Coordinator records the CREATING transition and broadcasts events

    The claim keeps two passes from starting the same session, so the handler takes
    no lock: a pass does not wait for another pass's create_kernels.
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
    def description(cls) -> str:
        return "Starts the kernels of sessions that passed the precondition check."

    @classmethod
    @override
    def target_statuses(cls) -> list[SessionStatus]:
        """Sessions in PREPARED state."""
        return [SessionStatus.PREPARED]

    @classmethod
    @override
    def target_kernel_statuses(cls) -> list[KernelStatus] | None:
        """Include sessions where kernels are in PREPARED status."""
        return [KernelStatus.PREPARED]

    @classmethod
    @override
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for start sessions handler (BEP-1030).

        - success: Session/kernel → CREATING (already set by the claim; a session that
          moved on during the pass, e.g. promoted to RUNNING or terminated, keeps its status)
        - need_retry: None (keeps the current status; a session reported as a failure
          must have its claim released first, or it stays CREATING and no pass retries it)
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
                except_session_statuses=frozenset(SessionStatus) - {SessionStatus.CREATING},
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
        """No lock: the claim in execute() keeps passes from starting a session twice.

        A lock held across create_kernels would make every later START pass wait for
        the slowest kernel creation in flight.
        """
        return None

    @override
    async def execute(
        self,
        _resource_group_id: ResourceGroupID,
        sessions: Sequence[SessionWithKernels],
    ) -> SessionExecutionResult:
        """Start kernels on agents for PREPARED sessions.

        The coordinator provides SessionWithKernels data.
        This handler:
        1. Claims the sessions; a session claimed by another pass is left out of the result
        2. Queries Repository for additional data (SessionDataForStart + ImageConfigData)
        3. Starts kernels on agents via Launcher
        """
        result = SessionExecutionResult()

        if not sessions:
            return result

        claimed_ids = await self._repository.claim_sessions_for_start(
            [s.session_info.identity.id for s in sessions],
            KernelLifecycleEventReason.TRIGGERED_BY_SCHEDULER,
        )
        sessions = [s for s in sessions if s.session_info.identity.id in claimed_ids]
        if not sessions:
            return result
        session_ids = [s.session_info.identity.id for s in sessions]

        # Query Repository for additional data needed by Launcher
        # Use search_sessions_with_kernels_and_user to get user info for session start
        searcher = SessionSearcher(
            pagination=NoPagination(),
            conditions=[
                SessionSearchableFields.own.id.filter.in_(
                    UUIDInMatchSpec(values=session_ids, negated=False)
                )
            ],
        )
        try:
            sessions_data = await self._repository.search_sessions_with_kernels_and_user(searcher)
        except BaseException:
            # Nothing was sent to the agents yet, so hand the sessions back to the next
            # pass; cancellation included, or the sessions would stay CREATING unstarted.
            await self._repository.release_sessions_for_start(session_ids)
            raise

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
                    reason=KernelLifecycleEventReason.TRIGGERED_BY_SCHEDULER,
                    creation_id=session_info.identity.creation_id,
                    access_key=AccessKey(session_info.metadata.access_key),
                )
            )

        return result
