from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiodocker import Docker

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.dependencies import DependencyProvider, HealthCheckerRegistration
from ai.backend.common.health_checker import HealthCheckKey
from ai.backend.common.health_checker.checkers import DockerHealthChecker
from ai.backend.common.health_checker.types import CONTAINER, ComponentId


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
    ) -> list[HealthCheckerRegistration]:
        """
        Return Docker health checker.

        Args:
            resource: The initialized Docker client

        Returns:
            List containing health checker registration for Docker
        """
        return [
            HealthCheckerRegistration(
                key=HealthCheckKey(service_group=CONTAINER, component_id=ComponentId("docker")),
                checker=DockerHealthChecker(docker=resource),
            )
        ]
