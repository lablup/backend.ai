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
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
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
    route_controller: RouteController


class RunningTransitionHook(StatusTransitionHook):
    """Hook executed when sessions transition to RUNNING status.

    Handles:
    - BATCH: Trigger batch execution
    - INFERENCE: Update route info and notify app proxy

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
            case SessionTypes.INFERENCE:
                await self._execute_inference_running(session)
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

    async def _execute_inference_running(self, session: SessionWithKernels) -> None:
        """Mark AppProxy resync needed for INFERENCE sessions reaching RUNNING.

        We do not push to AppProxy directly here. The route coordinator's
        APPPROXY_SYNC short cycle picks up the lifecycle hint and resyncs
        every endpoint that owns at least one HEALTHY route, so the
        AppProxy state becomes consistent regardless of which manager
        instance handled the transition.
        """
        session_id = session.session_info.identity.id
        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "finalize_start",
            success_detail="Session startup finalized",
        ):
            with recorder.step(
                "setup_route",
                success_detail="Marked AppProxy resync after RUNNING",
            ):
                await self._deps.route_controller.mark_lifecycle_needed(
                    RouteLifecycleType.APPPROXY_SYNC
                )
                log.info(
                    "Marked AppProxy resync after inference session {} reached RUNNING",
                    session_id,
                )


@dataclass
class TerminatedHookDependencies:
    """Dependencies for TerminatedTransitionHook."""

    route_controller: RouteController


class TerminatedTransitionHook(StatusTransitionHook):
    """Hook executed when sessions transition to TERMINATED status.

    Handles:
    - INFERENCE: Update route info (removal) and notify app proxy
    """

    _deps: TerminatedHookDependencies

    def __init__(self, deps: TerminatedHookDependencies) -> None:
        self._deps = deps

    async def execute(self, session: SessionWithKernels) -> None:
        """Execute TERMINATED transition hook."""
        session_type = session.session_info.metadata.session_type
        match session_type:
            case SessionTypes.INFERENCE:
                await self._execute_inference_terminated(session)
            case _:
                log.debug(
                    "No specific TERMINATED hook for session type {}",
                    session_type,
                )

    async def _execute_inference_terminated(self, session: SessionWithKernels) -> None:
        """Mark AppProxy resync needed for INFERENCE sessions reaching TERMINATED.

        Same rationale as the RUNNING hook: leave the actual Redis update
        and AppProxy fan-out to the route coordinator's APPPROXY_SYNC
        cycle, so a route that just lost its session falls out of the
        push set on the next sync.
        """
        session_id = session.session_info.identity.id
        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "finalize_termination",
            success_detail="Session termination finalized",
        ):
            with recorder.step(
                "cleanup_route",
                success_detail="Marked AppProxy resync after TERMINATED",
            ):
                await self._deps.route_controller.mark_lifecycle_needed(
                    RouteLifecycleType.APPPROXY_SYNC
                )
                log.info(
                    "Marked AppProxy resync after inference session {} reached TERMINATED",
                    session_id,
                )
