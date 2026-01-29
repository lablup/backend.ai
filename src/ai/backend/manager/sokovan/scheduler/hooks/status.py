"""Status-based transition hooks.

Hooks are organized by target status (RUNNING, TERMINATED, etc.)
and internally dispatch to session-type specific logic.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import AgentId, ResourceSlot, SessionId, SessionTypes
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.types import SessionRunningData, SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository

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

    scheduler_repository: SchedulerRepository
    agent_client_pool: AgentClientPool
    deployment_repository: DeploymentRepository
    event_producer: EventProducer


class RunningTransitionHook(StatusTransitionHook):
    """Hook executed when sessions transition to RUNNING status.

    Handles:
    - Common: Update agent occupied_slots
    - BATCH: Trigger batch execution
    - INFERENCE: Update route info and notify app proxy
    """

    _deps: RunningHookDependencies

    def __init__(self, deps: RunningHookDependencies) -> None:
        self._deps = deps

    async def execute(self, session: SessionWithKernels) -> None:
        """Execute RUNNING transition hook."""
        # 1. Common: Update occupied_slots for all session types
        await self._update_occupied_slots(session)

        # 2. Session-type specific logic
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

    async def _update_occupied_slots(self, session: SessionWithKernels) -> None:
        """Calculate and update occupied_slots for a session transitioning to RUNNING."""
        total_occupied_slots = ResourceSlot()
        for kernel_info in session.kernel_infos:
            if kernel_info.resource.occupied_slots:
                total_occupied_slots += kernel_info.resource.occupied_slots

        running_data = [
            SessionRunningData(
                session_id=session.session_info.identity.id,
                occupying_slots=total_occupied_slots,
            )
        ]
        await self._deps.scheduler_repository.update_sessions_to_running(running_data)
        log.debug(
            "Updated occupied_slots for session {} transitioning to RUNNING",
            session.session_info.identity.id,
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
                    batch_timeout = (
                        float(session.session_info.lifecycle.batch_timeout)
                        if session.session_info.lifecycle.batch_timeout is not None
                        else None
                    )
                    await client.trigger_batch_execution(
                        session_id,
                        main_kernel.id,
                        main_kernel.runtime.startup_command or "",
                        batch_timeout,
                    )
        log.info(
            "Successfully triggered batch execution for session {} on agent {}",
            session_id,
            agent_id,
        )

    async def _execute_inference_running(self, session: SessionWithKernels) -> None:
        """Create model service route for INFERENCE sessions."""
        from ai.backend.common.events.event_types.model_serving.anycast import (
            EndpointRouteListUpdatedEvent,
        )

        session_id = session.session_info.identity.id
        log.info(
            "Creating model service route for inference session {}",
            session_id,
        )

        # Get endpoint ID from session
        endpoint_id = await self._deps.deployment_repository.get_endpoint_id_by_session(session_id)
        if not endpoint_id:
            log.warning(
                "No endpoint ID found for inference session {}, skipping route update",
                session_id,
            )
            return

        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "finalize_start",
            success_detail="Session startup finalized",
        ):
            with recorder.step(
                "setup_route",
                success_detail=f"Set up route for endpoint {endpoint_id}",
            ):
                try:
                    # Update route info
                    await self._deps.deployment_repository.update_endpoint_route_info(endpoint_id)

                    # Send event to app proxy
                    await self._deps.event_producer.anycast_event(
                        EndpointRouteListUpdatedEvent(endpoint_id)
                    )

                    log.info(
                        "Successfully updated route info and notified app proxy for endpoint {} (session {})",
                        endpoint_id,
                        session_id,
                    )
                except Exception as e:
                    log.exception(
                        "Unexpected error updating route info for endpoint {} (session {}): {}",
                        endpoint_id,
                        session_id,
                        e,
                    )
                    raise


@dataclass
class TerminatedHookDependencies:
    """Dependencies for TerminatedTransitionHook."""

    deployment_repository: DeploymentRepository
    event_producer: EventProducer


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
        """Delete model service route for INFERENCE sessions."""
        from ai.backend.common.events.event_types.model_serving.anycast import (
            EndpointRouteListUpdatedEvent,
        )

        session_id = session.session_info.identity.id
        log.info(
            "Deleting model service route for inference session {}",
            session_id,
        )

        # Get endpoint ID from session
        endpoint_id = await self._deps.deployment_repository.get_endpoint_id_by_session(session_id)
        if not endpoint_id:
            log.warning(
                "No endpoint ID found for inference session {}, skipping route update",
                session_id,
            )
            return

        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(session_id)
        with recorder.phase(
            "finalize_termination",
            success_detail="Session termination finalized",
        ):
            with recorder.step(
                "cleanup_route",
                success_detail=f"Cleaned up route for endpoint {endpoint_id}",
            ):
                try:
                    # Update route info (removal)
                    await self._deps.deployment_repository.update_endpoint_route_info(endpoint_id)

                    # Send event to app proxy
                    await self._deps.event_producer.anycast_event(
                        EndpointRouteListUpdatedEvent(endpoint_id)
                    )

                    log.info(
                        "Successfully updated route info and notified app proxy of route removal for endpoint {} (session {})",
                        endpoint_id,
                        session_id,
                    )
                except Exception as e:
                    log.exception(
                        "Unexpected error updating route info for endpoint {} (session {}): {}",
                        endpoint_id,
                        session_id,
                        e,
                    )
                    raise
