from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import aiohttp

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.health.checkers.etcd import EtcdHealthChecker
from ai.backend.common.health.checkers.http import HttpHealthChecker
from ai.backend.common.health.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.health.probe import HealthProbe, HealthProbeOptions
from ai.backend.common.health.types import (
    DATABASE,
    ETCD,
    MANAGER,
    REDIS,
    ComponentId,
    HealthCheckKey,
    ServiceGroup,
)

from .database import DatabaseHealthChecker
from .docker import DockerHealthChecker
from .rpc import AgentRpcHealthChecker

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.client import AbstractValkeyClient
    from ai.backend.manager.clients.agent.client import AgentClient
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class ManagerHealthProbeArgs:
    db: ExtendedAsyncSAEngine
    valkey_client: AbstractValkeyClient
    etcd: AsyncEtcd
    storage_proxy_url: str
    agent_client: AgentClient
    timeout: float = 5.0


async def create_health_probe(args: ManagerHealthProbeArgs) -> HealthProbe:
    """
    Create and configure a HealthProbe for the Manager component.

    This function creates a HealthProbe instance and registers health checkers
    based on the provided dependencies.

    Args:
        args: Manager health probe configuration arguments

    Returns:
        HealthProbe instance with all checkers registered
    """
    probe = HealthProbe(HealthProbeOptions())

    # Register Database health checker
    await probe.register(
        HealthCheckKey(service_group=DATABASE, component_id=ComponentId("postgres")),
        DatabaseHealthChecker(db=args.db, timeout=args.timeout),
    )

    # Register Redis (Valkey) health checker
    await probe.register(
        HealthCheckKey(service_group=REDIS, component_id=ComponentId("valkey")),
        ValkeyHealthChecker(client=args.valkey_client, timeout=args.timeout),
    )

    # Register etcd health checker
    await probe.register(
        HealthCheckKey(service_group=ETCD, component_id=ComponentId("etcd")),
        EtcdHealthChecker(etcd=args.etcd, timeout=args.timeout),
    )

    # Register Docker health checker
    await probe.register(
        HealthCheckKey(service_group=MANAGER, component_id=ComponentId("docker")),
        DockerHealthChecker(timeout=args.timeout),
    )

    # Register Storage Proxy health checker
    await probe.register(
        HealthCheckKey(
            service_group=ServiceGroup("storage-proxy"),
            component_id=ComponentId("storage-proxy-http"),
        ),
        HttpHealthChecker(
            url=args.storage_proxy_url.rstrip("/") + "/status",
            session=aiohttp.ClientSession(),
            timeout=args.timeout,
        ),
    )

    # Register Agent RPC health checker
    await probe.register(
        HealthCheckKey(service_group=ServiceGroup("agent"), component_id=ComponentId("rpc")),
        AgentRpcHealthChecker(agent_client=args.agent_client, timeout=args.timeout),
    )

    return probe
