"""Session termination and sweep operations."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Final
from uuid import UUID

from ai.backend.common.clients.valkey_client.valkey_schedule import HealthCheckStatus
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import AgentId, KernelId, ResourceSlot, SessionId
from ai.backend.logging.structured import StructuredLogger, with_log_context
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.data.compute_cluster.types import ResourceGroupComputeCluster
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.errors.compute_cluster import ComputeClusterKubeconfigInvalid
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.compute_cluster import ComputeClusterResolver
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.views.sokovan.session import (
    KernelTerminationResult,
    TerminatingKernelData,
    TerminatingSessionData,
)

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class SessionTerminatorArgs:
    """Arguments for SessionTerminator initialization."""

    repository: SchedulerRepository
    agent_client_pool: AgentClientPool
    valkey_schedule: ValkeyScheduleClient
    compute_clusters: ComputeClusterResolver


COMPUTE_CLUSTER_GONE_REASON: Final = "compute-cluster-not-found"
"""The status reason of a kernel whose compute cluster was unregistered while it ended."""

COMPUTE_CLUSTER_INVALID_REASON: Final = "compute-cluster-invalid"
"""The status reason of a kernel whose compute cluster's stored kubeconfig no longer validates."""


async def _as_list[T](awaitable: Awaitable[T]) -> list[T]:
    return [await awaitable]


class SessionTerminator:
    """Handles termination and sweep operations for sessions and kernels."""

    _repository: SchedulerRepository
    _agent_client_pool: AgentClientPool
    _valkey_schedule: ValkeyScheduleClient
    _compute_clusters: ComputeClusterResolver

    def __init__(self, args: SessionTerminatorArgs) -> None:
        self._repository = args.repository
        self._agent_client_pool = args.agent_client_pool
        self._valkey_schedule = args.valkey_schedule
        self._compute_clusters = args.compute_clusters

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
            log.debug("no sessions to terminate")
            return ScheduleResult(
                scheduled_session_ids=[],
                scheduling_failures=[],
                reserved_session_ids=[],
                preemption_plan=[],
            )

        # One lookup for the batch: the agents that are the gateway of a compute cluster.
        agent_ids = {
            kernel.agent_id
            for session in terminating_sessions
            for kernel in session.kernels
            if kernel.agent_id
        }
        # The kernels of an agent whose lookup failed are retried in the next cycle.
        lookup = await self._compute_clusters.lookup_agents(agent_ids)
        compute_clusters = lookup.found

        # Collect all termination tasks from all sessions
        all_tasks: list[Awaitable[list[KernelTerminationResult]]] = []
        skipped_kernels = 0

        for session in terminating_sessions:
            cluster_kernels: list[TerminatingKernelData] = []
            found: ResourceGroupComputeCluster | None = None
            for kernel in session.kernels:
                # Only process kernels with assigned agents
                if not kernel.agent_id or kernel.agent_id in lookup.unresolved:
                    # No agent assigned (needs sweep), or its compute cluster is not known yet
                    skipped_kernels += 1
                    continue
                if (in_cluster := compute_clusters.get(kernel.agent_id)) is not None:
                    found = in_cluster
                    cluster_kernels.append(kernel)
                    continue
                all_tasks.append(
                    _as_list(
                        self._terminate_kernel(
                            kernel.agent_id,
                            kernel.kernel_id,
                            session.session_id,
                            session.status_info,
                            kernel.occupied_slots,
                        )
                    )
                )
            if found is not None:
                all_tasks.append(
                    self._terminate_in_compute_cluster(session, found, cluster_kernels)
                )

        # Kernels without agents will be handled by retry/timeout mechanism
        if skipped_kernels > 0:
            log.debug("kernels without agents left to retry", kernel_count=skipped_kernels)

        # Execute all termination tasks concurrently across all sessions
        if not all_tasks:
            log.debug("no kernels with agents to terminate")
            return ScheduleResult(
                scheduled_session_ids=[],
                scheduling_failures=[],
                reserved_session_ids=[],
                preemption_plan=[],
            )

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
        for task_results in results:
            if isinstance(task_results, BaseException):
                failed_count += 1
                continue
            for r in task_results:
                if r.success:
                    success_count += 1
                else:
                    failed_count += 1

        log.debug(
            "session termination requested",
            session_count=len(terminating_sessions),
            success_count=success_count,
            failure_count=failed_count,
        )

        return ScheduleResult(
            scheduled_session_ids=[],
            scheduling_failures=[],
            reserved_session_ids=[],
            preemption_plan=[],
        )

    async def _terminate_in_compute_cluster(
        self,
        session: TerminatingSessionData,
        found: ResourceGroupComputeCluster,
        kernels: list[TerminatingKernelData],
    ) -> list[KernelTerminationResult]:
        """Delete the session's workload once; that ends every kernel of the session.

        When the cluster's registration is gone, nothing is left to report the kernels' end,
        so they are marked terminated here instead of retrying forever.
        """
        with with_log_context(session_id=session.session_id):
            try:
                if found.cluster is None:
                    await self._repository.update_kernels_to_terminated(
                        [str(kernel.kernel_id) for kernel in kernels],
                        COMPUTE_CLUSTER_GONE_REASON,
                    )
                    log.warning(
                        "kernels marked terminated without a compute cluster",
                        resource_group=found.resource_group,
                        compute_cluster=found.cluster_name,
                        kernel_count=len(kernels),
                    )
                else:
                    async with self._compute_clusters.connect(found, found.cluster) as target:
                        await target.client.destroy_session(session.session_id, session.status_info)
                error = None
            except ComputeClusterKubeconfigInvalid as e:
                # Nothing can reach the cluster to end the kernels, as when it is gone.
                await self._repository.update_kernels_to_terminated(
                    [str(kernel.kernel_id) for kernel in kernels],
                    COMPUTE_CLUSTER_INVALID_REASON,
                )
                log.warning(
                    "kernels marked terminated with an invalid compute cluster kubeconfig",
                    resource_group=found.resource_group,
                    compute_cluster=found.cluster_name,
                    kernel_count=len(kernels),
                    exc_info=e,
                )
                error = None
            except Exception as e:
                log.warning(
                    "session workload deletion failed",
                    compute_cluster=found.cluster_name,
                    exc_info=e,
                )
                error = str(e)
        return [
            KernelTerminationResult(
                kernel_id=kernel.kernel_id,
                agent_id=kernel.agent_id,
                occupied_slots=kernel.occupied_slots,
                success=error is None,
                error=error,
            )
            for kernel in kernels
        ]

    async def _terminate_kernel(
        self,
        agent_id: AgentId,
        kernel_id: KernelId,
        session_id: SessionId,
        reason: KernelLifecycleEventReason,
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
        with with_log_context(session_id=session_id):
            try:
                async with self._agent_client_pool.acquire(agent_id) as client:
                    # Call agent's destroy_kernel RPC method with correct parameters
                    await client.destroy_kernel(
                        kernel_id, session_id, reason, suppress_events=False
                    )
                return KernelTerminationResult(
                    kernel_id=kernel_id,
                    agent_id=agent_id,
                    occupied_slots=occupied_slots,
                    success=True,
                )
            except Exception as e:
                log.warning(
                    "kernel termination failed",
                    kernel_id=kernel_id,
                    agent_id=agent_id,
                    exc_info=e,
                )
                return KernelTerminationResult(
                    kernel_id=kernel_id,
                    agent_id=agent_id,
                    occupied_slots=occupied_slots,
                    success=False,
                    error=str(e),
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
                    log.info(
                        "stale kernel found",
                        kernel_id=kernel_info.id,
                        session_id=kernel_info.session.session_id,
                    )
            except Exception as e:
                log.warning(
                    "kernel status check failed",
                    kernel_id=kernel_info.id,
                    session_id=kernel_info.session.session_id,
                    exc_info=e,
                )

        return dead_kernel_ids
