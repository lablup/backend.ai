"""Keeper for checking PREPARING/PULLING sessions."""

import asyncio
from collections import defaultdict

from ai.backend.common.types import SessionId
from ai.backend.manager.clients.agent.pool import AgentPool

from ..results import HealthCheckResult
from ..types import SessionData
from .base import HealthKeeper

# Time threshold for checking pulling sessions (15 minutes)
PULLING_CHECK_THRESHOLD = 900.0


class PullingHealthKeeper(HealthKeeper):
    """Keeper for checking PREPARING/PULLING sessions."""

    _agent_pool: AgentPool

    def __init__(self, agent_pool: AgentPool):
        self._agent_pool = agent_pool

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "pulling-health-check"

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
        return (current_time - oldest_status_change) >= PULLING_CHECK_THRESHOLD

    async def check_batch(
        self,
        sessions: list[SessionData],
    ) -> HealthCheckResult:
        """Check if image pulls are progressing for multiple sessions."""
        # Collect all unique images and their associated sessions
        image_to_sessions: defaultdict[str, list[SessionData]] = defaultdict(list)
        for session in sessions:
            kernel_images = {kernel.image for kernel in session.kernels if kernel.image}

            for image in kernel_images:
                image_to_sessions[image].append(session)

        # Batch check pull status for all images
        check_tasks: list[tuple[str, asyncio.Task[bool]]] = []

        for image, sessions_for_image in image_to_sessions.items():
            # Find an agent that might be pulling this image
            for session in sessions_for_image:
                agent_id = session.main_kernel.agent if session.main_kernel else None
                if agent_id:
                    agent_client = self._agent_pool.get_agent_client(agent_id)
                    task = asyncio.create_task(agent_client.check_pulling(image))
                    check_tasks.append((image, task))
                    break

        # Execute all checks and collect results
        image_active: dict[str, bool] = {}
        for image, task in check_tasks:
            try:
                is_active = await task
                image_active[image] = is_active
            except Exception:
                # On error, assume not active
                image_active[image] = False

        # Classify sessions based on whether their images are being pulled
        healthy_sessions: list[SessionId] = []
        unhealthy_sessions: list[SessionId] = []

        for session in sessions:
            kernel_images = {kernel.image for kernel in session.kernels if kernel.image}

            # If any image is still being pulled, session is healthy (operating)
            is_operating = any(image_active.get(image, False) for image in kernel_images)

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
        """Retry unhealthy sessions by restarting pull operations."""
        # TODO: Retry pull operations for unhealthy sessions
        pass
