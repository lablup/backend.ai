from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiodocker import Docker

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.dependencies import DependencyProvider


class DockerDependency(DependencyProvider[AgentUnifiedConfig, Docker]):
    """Provides Docker client lifecycle management.

    Creates a centralized Docker client instance that can be shared
    across the agent application, replacing ad-hoc Docker() instantiations.
    """

    @property
    def stage_name(self) -> str:
        return "docker"

    @asynccontextmanager
    async def provide(self, setup_input: AgentUnifiedConfig) -> AsyncIterator[Docker]:
        """Initialize and provide a Docker client.

        Args:
            setup_input: Agent unified configuration

        Yields:
            Initialized Docker client
        """
        docker = Docker()
        try:
            yield docker
        finally:
            await docker.close()
