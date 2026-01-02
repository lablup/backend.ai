"""Session termination and sweep operations."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Awaitable
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_schedule import HealthCheckStatus
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.types import AgentId, KernelId, ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.agent import AgentPool
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.scheduler import (
    KernelTerminationResult,
    SchedulerRepository,
)
from ai.backend.manager.scheduler.types import ScheduleType

from ..results import ScheduledSessionData, ScheduleResult
from ..types import SessionTransitionData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SessionTerminatorArgs:
    """Arguments for SessionTerminator initialization."""

    repository: SchedulerRepository
    agent_pool: AgentPool
    valkey_schedule: ValkeyScheduleClient


class SessionTerminator:
    """Handles termination and sweep operations for sessions and kernels."""

    _repository: SchedulerRepository
    _agent_pool: AgentPool
    _valkey_schedule: ValkeyScheduleClient

    def __init__(self, args: SessionTerminatorArgs) -> None:
        self._repository = args.repository
        self._agent_pool = args.agent_pool
        self._valkey_schedule = args.valkey_schedule

    async def terminate_sessions(self) -> ScheduleResult:
        """
        Send termination requests to all agents for sessions marked as TERMINATING.

        This method only sends RPC calls to agents. Actual status updates are handled by:
        - Agent event callbacks (for successful terminations)
        - sweep_lost_agent_kernels() (for lost agents or failed RPC calls)

        Returns:
            Empty ScheduleResult (no status updates performed here)
        """
        # Fetch all terminating sessions
        terminating_sessions = await self._repository.get_terminating_sessions()

        if not terminating_sessions:
            log.debug("No sessions to terminate")
            return ScheduleResult()

        log.info("Processing {} sessions for termination", len(terminating_sessions))

        # Collect all termination tasks from all sessions
        all_tasks: list[Awaitable[KernelTerminationResult]] = []
        skipped_kernels = 0

        for session in terminating_sessions:
            for kernel in session.kernels:
                # Only process kernels with assigned agents
                if kernel.agent_id:
                    task = self._terminate_kernel(
                        kernel.agent_id,
                        str(kernel.kernel_id),
                        str(session.session_id),
                        session.status_info,
                        kernel.occupied_slots,
                    )
                    all_tasks.append(task)
                else:
                    # Kernel has no agent assigned - needs sweep
                    skipped_kernels += 1

        # If there are kernels without agents, trigger sweep
        if skipped_kernels > 0:
            log.info(
                "Found {} kernels without agents, requesting sweep",
                skipped_kernels,
            )
            await self._valkey_schedule.mark_schedule_needed(
                ScheduleType.SWEEP_LOST_AGENT_KERNELS.value
            )

        # Execute all termination tasks concurrently across all sessions
        if not all_tasks:
            log.debug("No kernels with agents to terminate")
            return ScheduleResult()

        log.info("Terminating {} kernels in parallel", len(all_tasks))

        # Use gather with return_exceptions to ensure partial failures don't block others
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Log results but don't update DB (handled by events and sweep)
        success_count = 0
        failed_count = 0
        for r in results:
            if isinstance(r, BaseException):
                failed_count += 1
                continue
            if not r.success:
                failed_count += 1
                continue
            success_count += 1

        log.info(
            "Termination RPC calls completed: {} successful, {} failed",
            success_count,
            failed_count,
        )

        return ScheduleResult()

    async def _terminate_kernel(
        self,
        agent_id: AgentId,
        kernel_id: str,
        session_id: str,
        reason: str,
        occupied_slots: ResourceSlot,
    ) -> KernelTerminationResult:
        """
        Terminate a single kernel on an agent.

        :param agent_id: The agent ID where the kernel is running
        :param kernel_id: The kernel ID to terminate
        :param session_id: The session ID that owns the kernel
        :param reason: The reason for termination
        :return: KernelTerminationResult with success status
        """
        try:
            agent_client = self._agent_pool.get_agent_client(agent_id)

            # Call agent's destroy_kernel RPC method with correct parameters
            await agent_client.destroy_kernel(kernel_id, session_id, reason, suppress_events=False)
            return KernelTerminationResult(
                kernel_id=kernel_id,
                agent_id=agent_id,
                occupied_slots=occupied_slots,
                success=True,
            )
        except Exception as e:
            log.warning(
                "Failed to terminate kernel {} on agent {}: {}",
                kernel_id,
                agent_id,
                e,
            )

            return KernelTerminationResult(
                kernel_id=kernel_id,
                agent_id=agent_id,
                occupied_slots=occupied_slots,
                success=False,
                error=str(e),
            )

    async def sweep_stale_sessions(self) -> ScheduleResult:
        """
        Sweep stale sessions including those with pending timeout.
        This is a maintenance operation, not a scheduling operation.

        Note: The actual marking of sessions for termination should be done
        through SchedulingController.mark_sessions_for_termination() by the coordinator.

        :return: ScheduleResult with the count of swept sessions
        """
        # Get sessions that have exceeded their pending timeout
        timed_out_sessions = await self._repository.get_pending_timeout_sessions()

        if timed_out_sessions:
            # Extract session IDs
            session_ids = [session.session_id for session in timed_out_sessions]

            log.info(
                "Found {} sessions with pending timeout that need termination",
                len(session_ids),
            )

            # Note: The coordinator should call SchedulingController.mark_sessions_for_termination()
            # with these session_ids. This method just identifies the sessions.
            # For now, we'll directly mark them through repository for backward compatibility
            await self._repository.mark_sessions_terminating(
                session_ids,
                reason="PENDING_TIMEOUT",
            )

            # Convert swept sessions to ScheduledSessionData format
            scheduled_data = [
                ScheduledSessionData(
                    session_id=session.session_id,
                    creation_id=session.creation_id,
                    access_key=session.access_key,
                    reason="sweeped-as-stale",
                )
                for session in timed_out_sessions
            ]
            return ScheduleResult(scheduled_sessions=scheduled_data)

        return ScheduleResult()

    async def sweep_lost_agent_kernels(self) -> ScheduleResult:
        """
        Sweep kernels in TERMINATING sessions that cannot be terminated normally.

        This handles kernels where:
        - Agent is LOST
        - Agent is None (never assigned)

        These kernels are directly marked as TERMINATED without RPC calls.
        This is a cleanup operation separate from normal termination.
        Only kernel status is updated; session status updates are handled
        by other mechanisms when all kernels are terminated.

        Returns:
            ScheduleResult (empty - no scheduled sessions)
        """
        # Fetch kernels with lost or missing agents
        lost_kernels = await self._repository.get_terminating_kernels_with_lost_agents()

        if not lost_kernels:
            log.debug("No lost agent kernels to sweep")
            return ScheduleResult()

        log.info(
            "Sweeping {} kernels with lost/missing agents",
            len(lost_kernels),
        )

        # Build kernel results
        kernel_results: list[KernelTerminationResult] = []

        for kernel in lost_kernels:
            log.info(
                "Sweeping kernel {} in session {} (agent: {}, agent_status: {})",
                kernel.kernel_id,
                kernel.session_id,
                kernel.agent_id,
                kernel.agent_status,
            )

            # Mark as successfully terminated since agent is gone
            kernel_result = KernelTerminationResult(
                kernel_id=kernel.kernel_id,
                agent_id=kernel.agent_id,
                occupied_slots=ResourceSlot(),  # Empty since agent is lost/missing
                success=True,
            )
            kernel_results.append(kernel_result)

        # Batch update all swept kernels (sessions will be updated by other handlers)
        await self._repository.batch_update_kernels_terminated(
            kernel_results,
            reason="swept-lost-agent",
        )

        log.info("Successfully swept {} kernels", len(kernel_results))

        # Request check-terminating-progress to update session status
        await self._valkey_schedule.mark_schedule_needed(
            ScheduleType.CHECK_TERMINATING_PROGRESS.value
        )

        return ScheduleResult()

    async def sweep_stale_kernels(self) -> ScheduleResult:
        """
        Sweep kernels with stale presence status.
        Only updates kernel status to TERMINATED, does NOT change session status.

        :return: ScheduleResult with affected sessions for post-processing
        """
        # 1. Get RUNNING sessions with RUNNING kernels
        running_sessions = await self._repository.get_sessions_for_transition(
            session_statuses=[SessionStatus.RUNNING],
            kernel_statuses=[KernelStatus.RUNNING],
        )
        if not running_sessions:
            return ScheduleResult()

        # 2. Extract kernel IDs and agent IDs, then check presence status in Redis
        running_kernel_ids: list[KernelId] = []
        agent_ids: set[AgentId] = set()
        for session in running_sessions:
            for kernel in session.kernels:
                running_kernel_ids.append(KernelId(UUID(kernel.kernel_id)))
                agent_ids.add(kernel.agent_id)
        statuses = await self._valkey_schedule.check_kernel_presence_status_batch(
            running_kernel_ids,
            agent_ids=agent_ids,
        )

        # 3. Filter STALE kernels (None status or STALE presence)
        stale_kernel_id_set: set[str] = {
            str(kernel_id)
            for kernel_id in running_kernel_ids
            if (status := statuses.get(kernel_id)) is None
            or status.presence == HealthCheckStatus.STALE
        }
        if not stale_kernel_id_set:
            return ScheduleResult()

        # 4. Check with agent RPC - only explicit False terminates
        dead_kernel_ids: list[str] = []
        affected_sessions: list[SessionTransitionData] = []

        for session in running_sessions:
            for kernel in session.kernels:
                if kernel.kernel_id not in stale_kernel_id_set:
                    continue
                try:
                    agent_client = self._agent_pool.get_agent_client(kernel.agent_id)
                    is_running = await agent_client.check_running(kernel.kernel_id)
                    if is_running is False:
                        dead_kernel_ids.append(kernel.kernel_id)
                        if session not in affected_sessions:
                            affected_sessions.append(session)
                except Exception as e:
                    log.warning(
                        "Failed to check kernel {} status: {}. Skipping.",
                        kernel.kernel_id,
                        e,
                    )

        if not dead_kernel_ids:
            return ScheduleResult()

        # 5. Update kernel status to TERMINATED (NOT session status)
        updated_count = await self._repository.update_kernels_to_terminated(
            dead_kernel_ids, reason="STALE_KERNEL"
        )
        log.info("Marked {} stale kernels as TERMINATED", updated_count)

        # 6. Return result for post_process to trigger CHECK_RUNNING_SESSION_TERMINATION
        return ScheduleResult(
            scheduled_sessions=[
                ScheduledSessionData(
                    session_id=s.session_id,
                    creation_id=s.creation_id,
                    access_key=s.access_key,
                    reason="STALE_KERNEL",
                )
                for s in affected_sessions
            ]
        )
