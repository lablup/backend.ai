from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.clients.agent import AgentClientPool, AgentPoolSpec


@dataclass
class AgentClientPoolInput:
    """Input required for agent client pool setup."""

    agent_cache: AgentRPCCache


class AgentClientPoolDependency(
    NonMonitorableDependencyProvider[AgentClientPoolInput, AgentClientPool],
):
    """Provides AgentClientPool lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "agent-client-pool"

    @asynccontextmanager
    async def provide(self, setup_input: AgentClientPoolInput) -> AsyncIterator[AgentClientPool]:
        """Initialize and provide an agent client pool.

        Args:
            setup_input: Input containing agent RPC cache

        Yields:
            Initialized AgentClientPool
        """
        pool = AgentClientPool(
            setup_input.agent_cache,
            AgentPoolSpec(
                health_check_interval=30.0,
                failure_threshold=3,
                recovery_timeout=60.0,
            ),
        )
        try:
            yield pool
        finally:
            await pool.close()
