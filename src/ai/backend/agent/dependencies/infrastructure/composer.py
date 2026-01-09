from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from aiodocker import Docker

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd

from .docker import DockerDependency
from .redis import AgentValkeyClients, AgentValkeyDependency


@dataclass
class AgentInfrastructureInput:
    """Input required for agent infrastructure setup.

    Contains the unified configuration, etcd client, and redis config
    from the bootstrap stage.
    """

    config: AgentUnifiedConfig
    etcd: AsyncEtcd
    redis_config: RedisConfig


@dataclass
class AgentInfrastructureResources:
    """Container for all initialized agent infrastructure resources.

    Holds initialized foundational dependencies (etcd, valkey clients, docker)
    that are used throughout the agent lifecycle or CLI execution.
    """

    etcd: AsyncEtcd
    valkey: AgentValkeyClients
    docker: Docker


class AgentInfrastructureComposer(
    DependencyComposer[AgentInfrastructureInput, AgentInfrastructureResources]
):
    """Composes all agent infrastructure dependencies as a single unit.

    Composes valkey and docker dependencies in order.
    Etcd is passed from the bootstrap stage and not managed here.
    """

    @property
    def stage_name(self) -> str:
        return "infrastructure"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: AgentInfrastructureInput,
    ) -> AsyncIterator[AgentInfrastructureResources]:
        """Compose all infrastructure dependencies.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Infrastructure input containing config and etcd client

        Yields:
            AgentInfrastructureResources containing all initialized resources
        """
        # Enter dependencies using the stack
        valkey = await stack.enter_dependency(
            AgentValkeyDependency(),
            setup_input.redis_config,
        )
        docker = await stack.enter_dependency(
            DockerDependency(),
            setup_input.config,
        )

        # Yield the infrastructure resources
        yield AgentInfrastructureResources(
            etcd=setup_input.etcd,
            valkey=valkey,
            docker=docker,
        )
