"""Session termination and sweep operations."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import dataclass
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_schedule import HealthCheckStatus
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.types import AgentId, KernelId, ResourceSlot, SessionId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.repositories.scheduler import (
    KernelTerminationResult,
    SchedulerRepository,
    TerminatingKernelWithAgentData,
    TerminatingSessionData,
)
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels, SweepStaleKernelsResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SessionTerminatorArgs:
    """Arguments for SessionTerminator initialization."""

    repository: SchedulerRepository
    agent_client_pool: AgentClientPool
    valkey_schedule: ValkeyScheduleClient


class SessionTerminator:
    """Handles termination and sweep operations for sessions and kernels."""

    _repository: SchedulerRepository
    _agent_client_pool: AgentClientPool
    _valkey_schedule: ValkeyScheduleClient

    def __init__(self, args: SessionTerminatorArgs) -> None:
        self._repository = args.repository
        self._agent_client_pool = args.agent_client_pool
        self._valkey_schedule = args.valkey_schedule

    async def terminate_sessions_for_handler(
        self,
        terminating_sessions: list[TerminatingSessionData],
    ) -> None:
        """
        Send termination requests for the given sessions.

        Handler-specific method that works with pre-fetched data.
        Used by TerminateSessionsLifecycleHandler.

        :param terminating_sessions: List of sessions to terminate with kernel details
        """
        await self._terminate_sessions_internal(terminating_sessions)

    async def _terminate_sessions_internal(
        self,
        terminating_sessions: list[TerminatingSessionData],
    ) -> ScheduleResult:
        """
        Internal implementation for terminating sessions.

        :param terminating_sessions: List of sessions to terminate
        :return: Empty ScheduleResult (no status updates performed here)
        """
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
                        kernel.kernel_id,
                        session.session_id,
                        session.status_info,
                        kernel.occupied_slots,
                    )
                    all_tasks.append(task)
                else:
                    # Kernel has no agent assigned - needs sweep
                    skipped_kernels += 1

        # Kernels without agents will be handled by retry/timeout mechanism
        if skipped_kernels > 0:
            log.info(
                "Found {} kernels without agents, will be handled by retry/timeout",
                skipped_kernels,
            )

        # Execute all termination tasks concurrently across all sessions
        if not all_tasks:
            log.debug("No kernels with agents to terminate")
            return ScheduleResult()

        log.info("Terminating {} kernels in parallel", len(all_tasks))

        # Use gather with return_exceptions to ensure partial failures don't block others
        with RecorderContext[SessionId].shared_phase(
            "kernel_destruction",
            success_detail="Kernels terminating",
        ):
            with RecorderContext[SessionId].shared_step(
                "destroy_kernels",
                success_detail="Kernel destruction requested",
            ):
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
        kernel_id: KernelId,
        session_id: SessionId,
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
            async with self._agent_client_pool.acquire(agent_id) as client:
                # Call agent's destroy_kernel RPC method with correct parameters
                await client.destroy_kernel(kernel_id, session_id, reason, suppress_events=False)
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

    async def sweep_lost_agent_kernels_for_handler(
        self,
        lost_kernels: list[TerminatingKernelWithAgentData],
    ) -> list[KernelTerminationResult]:
        """
        Sweep kernels with lost/missing agents from given list.

        Handler-specific method that works with pre-fetched data.
        Legacy method - retained for backward compatibility.

        Note: This method only returns kernel termination results.
        The Coordinator is responsible for applying the status changes.

        :param lost_kernels: List of kernels with lost agents
        :return: List of kernel termination results for Coordinator to process
        """
        if not lost_kernels:
            return []

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

        return kernel_results

    async def sweep_stale_kernels_for_handler(
        self,
        sessions: list[SessionWithKernels],
    ) -> SweepStaleKernelsResult:
        """
        Sweep stale kernels from given sessions.

        Handler-specific method that works with SessionWithKernels data.
        Legacy method - retained for backward compatibility.
        Note: Use check_stale_kernels() for KernelLifecycleHandler.

        Note: This method only detects stale kernels and returns the results.
        The Coordinator is responsible for applying the status changes.

        :param sessions: List of RUNNING sessions to check for stale kernels
        :return: Result containing dead kernel IDs and affected sessions
        """
        empty_result = SweepStaleKernelsResult(
            dead_kernel_ids=[],
            affected_sessions=[],
        )

        if not sessions:
            return empty_result

        # 1. Extract kernel IDs and agent IDs, then check presence status
        running_kernel_ids: list[KernelId] = []
        agent_ids: set[AgentId] = set()
        for session in sessions:
            for kernel_info in session.kernel_infos:
                running_kernel_ids.append(KernelId(kernel_info.id))
                if kernel_info.resource.agent:
                    agent_ids.add(AgentId(kernel_info.resource.agent))

        if not running_kernel_ids:
            return empty_result

        with RecorderContext[SessionId].shared_phase(
            "verify_kernel_liveness",
            success_detail="Kernel liveness verification completed",
        ):
            with RecorderContext[SessionId].shared_step(
                "check_kernel_presence",
                success_detail="Kernel presence checked",
            ):
                statuses = await self._valkey_schedule.check_kernel_presence_status_batch(
                    running_kernel_ids,
                    agent_ids=agent_ids,
                )

        # 2. Filter STALE kernels (None status or STALE presence)
        stale_kernel_id_set: set[UUID] = {
            kernel_id
            for kernel_id in running_kernel_ids
            if (status := statuses.get(kernel_id)) is None
            or status.presence == HealthCheckStatus.STALE
        }
        if not stale_kernel_id_set:
            return empty_result

        # 3. Check with agent - only explicit False terminates
        dead_kernel_ids: list[KernelId] = []
        affected_sessions: list[SessionWithKernels] = []
        pool = RecorderContext[SessionId].current_pool()

        for session in sessions:
            for kernel_info in session.kernel_infos:
                if kernel_info.id not in stale_kernel_id_set:
                    continue
                if not kernel_info.resource.agent:
                    continue
                try:
                    recorder = pool.recorder(session.session_info.identity.id)
                    with recorder.phase(
                        "verify_kernel_liveness",
                        success_detail="Kernel liveness verified",
                    ):
                        with recorder.step(
                            "confirm_with_agent",
                            success_detail=f"Kernel {kernel_info.id} status confirmed",
                        ):
                            agent_id = AgentId(kernel_info.resource.agent)
                            async with self._agent_client_pool.acquire(agent_id) as client:
                                is_running = await client.check_running(kernel_info.id)
                            if is_running is False:
                                dead_kernel_ids.append(KernelId(kernel_info.id))
                                if session not in affected_sessions:
                                    affected_sessions.append(session)
                except Exception as e:
                    log.warning(
                        "Failed to check kernel {} status: {}. Skipping.",
                        kernel_info.id,
                        e,
                    )

        if not dead_kernel_ids:
            return empty_result

        log.info("Found {} stale kernels to be terminated", len(dead_kernel_ids))

        return SweepStaleKernelsResult(
            dead_kernel_ids=dead_kernel_ids,
            affected_sessions=affected_sessions,
        )

    async def check_stale_kernels(
        self,
        kernels: list[KernelInfo],
    ) -> list[KernelId]:
        """
        Check for stale kernels from given kernel list.

        Kernel handler-specific method that works with KernelInfo directly.
        Used by SweepStaleKernelsKernelHandler.

        This method:
        1. Checks kernel presence status in Valkey
        2. For potentially stale kernels, confirms with agent if truly dead
        3. Returns list of kernel IDs that are confirmed dead

        :param kernels: List of RUNNING kernels to check for staleness
        :return: List of kernel IDs that are dead/stale
        """
        if not kernels:
            return []

        # 1. Extract kernel IDs and agent IDs
        kernel_ids: list[KernelId] = []
        agent_ids: set[AgentId] = set()
        for kernel_info in kernels:
            kernel_ids.append(KernelId(kernel_info.id))
            if kernel_info.resource.agent:
                agent_ids.add(AgentId(kernel_info.resource.agent))

        if not kernel_ids:
            return []

        # 2. Check presence status in Valkey
        statuses = await self._valkey_schedule.check_kernel_presence_status_batch(
            kernel_ids,
            agent_ids=agent_ids,
        )

        # 3. Filter STALE kernels (None status or STALE presence)
        stale_kernel_id_set: set[UUID] = {
            kernel_id
            for kernel_id in kernel_ids
            if (status := statuses.get(kernel_id)) is None
            or status.presence == HealthCheckStatus.STALE
        }
        if not stale_kernel_id_set:
            return []

        # 4. Check with agent - only explicit False terminates
        dead_kernel_ids: list[KernelId] = []

        for kernel_info in kernels:
            if kernel_info.id not in stale_kernel_id_set:
                continue
            if not kernel_info.resource.agent:
                continue
            try:
                agent_id = AgentId(kernel_info.resource.agent)
                async with self._agent_client_pool.acquire(agent_id) as client:
                    is_running = await client.check_running(kernel_info.id)
                if is_running is False:
                    dead_kernel_ids.append(KernelId(kernel_info.id))
            except Exception as e:
                log.warning(
                    "Failed to check kernel {} status: {}. Skipping.",
                    kernel_info.id,
                    e,
                )

        if dead_kernel_ids:
            log.info("Found {} stale kernels to be terminated", len(dead_kernel_ids))

        return dead_kernel_ids
