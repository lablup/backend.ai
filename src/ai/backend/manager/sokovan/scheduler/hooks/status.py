"""Status-based transition hooks.

Hooks are organized by target status (RUNNING, TERMINATED, etc.)
and internally dispatch to session-type specific logic.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.types import (
    AgentId,
    SessionId,
    SessionTypes,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.sokovan.data import SessionWithKernels
from ai.backend.manager.sokovan.recorder.context import RecorderContext

log = BraceStyleAdapter(logging.getLogger(__name__))


class StatusTransitionHook(ABC):
    """Base class for status-based transition hooks.

    Each subclass handles a specific target status (RUNNING, TERMINATED, etc.)
    and internally dispatches to session-type specific logic.
    """

    @abstractmethod
    async def execute(self, session: SessionWithKernels) -> None:
        """Execute the hook for a session transitioning to this status.

        Args:
            session: The session with kernel information
        """
        raise NotImplementedError


@dataclass
class RunningHookDependencies:
    """Dependencies for RunningTransitionHook."""

    agent_client_pool: AgentClientPool


class RunningTransitionHook(StatusTransitionHook):
    """Hook executed when sessions transition to RUNNING status.

    Handles:
    - BATCH: Trigger batch execution
    - INFERENCE: no-op — the route coordinator pushes to AppProxy
      synchronously from the health-check handler when a route first
      transitions to HEALTHY, and the long-cycle ``AppProxySyncRouteHandler``
      keeps state convergent as a fallback.

    Note: Resource allocation (occupied_slots) is handled per-kernel at
    kernel RUNNING transition time, not here at session level.
    """

    _deps: RunningHookDependencies

    def __init__(self, deps: RunningHookDependencies) -> None:
        self._deps = deps

    async def execute(self, session: SessionWithKernels) -> None:
        """Execute RUNNING transition hook.

        Note: Resource allocation is now handled per-kernel at kernel RUNNING
        transition time (in update_kernel_status_running), not here at
        session RUNNING transition time.
        """
        # Session-type specific logic
        session_type = session.session_info.metadata.session_type
        match session_type:
            case SessionTypes.BATCH:
                await self._execute_batch(session)
            case _:
                log.debug(
                    "No specific RUNNING hook for session type {}",
                    session_type,
                )

    async def _execute_batch(self, session: SessionWithKernels) -> None:
        """Trigger batch execution for BATCH sessions."""
        main_kernel = session.main_kernel
        agent_id = AgentId(main_kernel.resource.agent) if main_kernel.resource.agent else None
        if agent_id is None:
            raise ValueError(
                f"Main kernel has no agent assigned for session {session.session_info.identity.id}"
            )

        session_id = session.session_info.identity.id
        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "finalize_start",
            success_detail="Session startup finalized",
        ):
            with recorder.step(
                "trigger_batch_execution",
                success_detail=f"Triggered batch execution on agent {agent_id}",
            ):
                async with self._deps.agent_client_pool.acquire(agent_id) as client:
                    session_batch_timeout = session.session_info.lifecycle.batch_timeout
                    await client.trigger_batch_execution(
                        session_id,
                        main_kernel.id,
                        main_kernel.runtime.startup_command or "",
                        float(session_batch_timeout) if session_batch_timeout is not None else None,
                    )
        log.info(
            "Successfully triggered batch execution for session {} on agent {}",
            session_id,
            agent_id,
        )


@dataclass
class TerminatedHookDependencies:
    """Dependencies for TerminatedTransitionHook (currently empty).

    Kept as a placeholder so adding new TERMINATED-specific hooks does
    not require re-threading dependency injection wiring.
    """


class TerminatedTransitionHook(StatusTransitionHook):
    """Hook executed when sessions transition to TERMINATED status.

    Currently a no-op for every session type. Inference termination
    used to mark APPPROXY_SYNC needed; that is no longer required
    because :class:`TerminatingRouteHandler` unregisters routes from
    AppProxy synchronously before destroying kernels, and the long-
    cycle ``AppProxySyncRouteHandler`` keeps state convergent as a
    fallback.
    """

    _deps: TerminatedHookDependencies

    def __init__(self, deps: TerminatedHookDependencies) -> None:
        self._deps = deps

    async def execute(self, session: SessionWithKernels) -> None:
        """Execute TERMINATED transition hook."""
        log.debug(
            "TERMINATED transition hook is currently a no-op for session type {}",
            session.session_info.metadata.session_type,
        )
