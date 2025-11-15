from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.defs import (
    REDIS_BGTASK_DB,
    REDIS_CONTAINER_LOG,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    RedisRole,
)
from ai.backend.common.dependencies import DependencyProvider, HealthCheckerRegistration
from ai.backend.common.health_checker import HealthCheckKey
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.health_checker.types import REDIS, ComponentId


@dataclass
class AgentValkeyClients:
    """Container for agent-specific Valkey client instances.

    Agent uses 4 specialized clients for operational needs.
    """

    stat: ValkeyStatClient
    stream: ValkeyStreamClient
    bgtask: ValkeyBgtaskClient
    container_log: ValkeyContainerLogClient

    async def close(self) -> None:
        """Close all Valkey client connections."""
        await self.stat.close()
        await self.stream.close()
        await self.bgtask.close()
        await self.container_log.close()


class AgentValkeyDependency(DependencyProvider[RedisConfig, AgentValkeyClients]):
    """Provides lifecycle management for 4 agent-specific Valkey clients."""

    @property
    def stage_name(self) -> str:
        return "valkey"

    @asynccontextmanager
    async def provide(self, setup_input: RedisConfig) -> AsyncIterator[AgentValkeyClients]:
        """Initialize and provide all agent Valkey clients.

        Args:
            setup_input: Redis configuration from etcd

        Yields:
            AgentValkeyClients instance containing 4 specialized clients
        """
        valkey_profile_target = setup_input.to_valkey_profile_target()

        # Create 4 specialized clients needed by agent
        clients = AgentValkeyClients(
            stat=await ValkeyStatClient.create(
                valkey_profile_target.profile_target(RedisRole.STATISTICS),
                db_id=REDIS_STATISTICS_DB,
                human_readable_name="agent.stat",
            ),
            stream=await ValkeyStreamClient.create(
                valkey_profile_target.profile_target(RedisRole.STREAM),
                db_id=REDIS_STREAM_DB,
                human_readable_name="agent.stream",
            ),
            bgtask=await ValkeyBgtaskClient.create(
                valkey_profile_target.profile_target(RedisRole.BGTASK),
                db_id=REDIS_BGTASK_DB,
                human_readable_name="agent.bgtask",
            ),
            container_log=await ValkeyContainerLogClient.create(
                valkey_profile_target.profile_target(RedisRole.CONTAINER_LOG),
                db_id=REDIS_CONTAINER_LOG,
                human_readable_name="agent.container_log",
            ),
        )

        try:
            yield clients
        finally:
            await clients.close()

    def gen_health_checkers(self, resource: AgentValkeyClients) -> list[HealthCheckerRegistration]:
        """
        Return health checkers for all 4 agent Valkey clients.

        Args:
            resource: The initialized Valkey clients

        Returns:
            List of health checker registrations for all 4 Valkey clients
        """
        return [
            HealthCheckerRegistration(
                key=HealthCheckKey(service_group=REDIS, component_id=ComponentId("stat")),
                checker=ValkeyHealthChecker(client=resource.stat),
            ),
            HealthCheckerRegistration(
                key=HealthCheckKey(service_group=REDIS, component_id=ComponentId("stream")),
                checker=ValkeyHealthChecker(client=resource.stream),
            ),
            HealthCheckerRegistration(
                key=HealthCheckKey(service_group=REDIS, component_id=ComponentId("bgtask")),
                checker=ValkeyHealthChecker(client=resource.bgtask),
            ),
            HealthCheckerRegistration(
                key=HealthCheckKey(service_group=REDIS, component_id=ComponentId("container_log")),
                checker=ValkeyHealthChecker(client=resource.container_log),
            ),
        ]
