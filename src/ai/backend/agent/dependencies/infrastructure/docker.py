from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiodocker import Docker

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.health import DockerHealthChecker
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import ServiceHealthChecker


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

    def gen_health_checkers(
        self,
        resource: Docker,
    ) -> ServiceHealthChecker:
        """
        Return Docker health checker.

        Args:
            resource: The initialized Docker client

        Returns:
            DockerHealthChecker for Docker
        """
        return DockerHealthChecker(docker=resource)
