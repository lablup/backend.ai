from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from aiodocker import Docker

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.clients.valkey_client.sentinel_monitor.dependency import (
    SentinelMonitorDependency,
)
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd

from .docker import DockerDependency
from .redis import AgentValkeyClients, AgentValkeyDependency, AgentValkeyInput


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

    Composes Sentinel monitor, valkey and docker dependencies in order.
    Etcd is passed from the bootstrap stage and not managed here.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "infrastructure"

    @asynccontextmanager
    @override
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
        sentinel_monitors = await stack.enter_dependency(
            SentinelMonitorDependency(),
            setup_input.redis_config.to_valkey_profile_target().targets(),
        )
        valkey = await stack.enter_dependency(
            AgentValkeyDependency(),
            AgentValkeyInput(
                redis_config=setup_input.redis_config, sentinel_monitors=sentinel_monitors
            ),
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
