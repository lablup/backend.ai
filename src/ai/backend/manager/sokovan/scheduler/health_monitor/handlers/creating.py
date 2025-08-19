"""Keeper for checking CREATING sessions."""

import asyncio

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.clients.agent.pool import AgentPool

from ..results import HealthCheckResult
from ..types import SessionData
from .base import HealthKeeper

# Time threshold for checking creating sessions (10 minutes)
CREATING_CHECK_THRESHOLD = 600.0


class CreatingHealthKeeper(HealthKeeper):
    """Keeper for checking CREATING sessions."""

    _agent_pool: AgentPool

    def __init__(self, agent_pool: AgentPool):
        self._agent_pool = agent_pool

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "creating-health-check"

    def need_check(self, session: SessionData, current_time: float) -> bool:
        """Check if session needs health check based on time threshold."""
        # Check the oldest kernel's status_changed time
        oldest_status_change = min(
            (kernel.status_changed for kernel in session.kernels if kernel.status_changed),
            default=None,
        )

        if oldest_status_change is None:
            # No status change info, always check
            return True

        # Check if enough time has passed since last status change
        return (current_time - oldest_status_change) >= CREATING_CHECK_THRESHOLD

    async def check_batch(
        self,
        sessions: list[SessionData],
    ) -> HealthCheckResult:
        """Check if kernel creation is progressing for multiple sessions."""
        # Collect all kernels with their sessions
        check_tasks: list[tuple[KernelId, asyncio.Task[bool]]] = []
        kernel_to_session: dict[KernelId, SessionData] = {}

        for session in sessions:
            for kernel in session.kernels:
                if kernel.agent:
                    agent_client = self._agent_pool.get_agent_client(kernel.agent)
                    task = asyncio.create_task(agent_client.check_creating(str(kernel.id)))
                    check_tasks.append((kernel.id, task))
                    kernel_to_session[kernel.id] = session

        # Execute all checks and collect results
        kernel_active: dict[KernelId, bool] = {}
        for kernel_id, task in check_tasks:
            try:
                is_active = await task
                kernel_active[kernel_id] = is_active
            except Exception:
                # On error, assume not active
                kernel_active[kernel_id] = False

        # Classify sessions based on whether their kernels are being created
        healthy_sessions: list[SessionId] = []
        unhealthy_sessions: list[SessionId] = []

        for session in sessions:
            # If any kernel is still being created, session is healthy (operating)
            is_operating = any(
                kernel_active.get(kernel.id, False) for kernel in session.kernels if kernel.agent
            )

            if is_operating:
                healthy_sessions.append(session.id)
            else:
                unhealthy_sessions.append(session.id)

        return HealthCheckResult(
            healthy_sessions=healthy_sessions,
            unhealthy_sessions=unhealthy_sessions,
        )

    async def retry_unhealthy_sessions(
        self,
        unhealthy_sessions: list[SessionId],
    ) -> None:
        """Retry unhealthy sessions by restarting kernel creation."""
        # TODO: Retry kernel creation for unhealthy sessions
        pass
