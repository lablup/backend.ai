from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.health.checkers.etcd import EtcdHealthChecker
from ai.backend.common.health.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.health.probe import HealthProbe, HealthProbeOptions
from ai.backend.common.health.types import (
    AGENT,
    ETCD,
    REDIS,
    ComponentId,
    HealthCheckKey,
)

from .docker import DockerHealthChecker

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.client import AbstractValkeyClient


@dataclass
class AgentHealthProbeArgs:
    valkey_client: AbstractValkeyClient
    etcd: AsyncEtcd
    timeout: float = 5.0


async def create_health_probe(args: AgentHealthProbeArgs) -> HealthProbe:
    """
    Create and configure a HealthProbe for the Agent component.

    This function creates a HealthProbe instance and registers health checkers
    based on the provided dependencies.

    Args:
        args: Agent health probe configuration arguments

    Returns:
        HealthProbe instance with all checkers registered
    """
    probe = HealthProbe(HealthProbeOptions())

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
        HealthCheckKey(service_group=AGENT, component_id=ComponentId("docker")),
        DockerHealthChecker(timeout=args.timeout),
    )

    return probe
