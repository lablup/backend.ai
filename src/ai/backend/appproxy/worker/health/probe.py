from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import aiohttp

from ai.backend.common.health.checkers.http import HttpHealthChecker
from ai.backend.common.health.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.health.probe import HealthProbe, HealthProbeOptions
from ai.backend.common.health.types import (
    REDIS,
    ComponentId,
    HealthCheckKey,
    ServiceGroup,
)

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.client import AbstractValkeyClient


@dataclass
class WorkerHealthProbeArgs:
    valkey_client: AbstractValkeyClient
    coordinator_url: str
    timeout: float = 5.0


async def create_health_probe(args: WorkerHealthProbeArgs) -> HealthProbe:
    """
    Create and configure a HealthProbe for the App Proxy Worker component.

    This function creates a HealthProbe instance and registers health checkers
    based on the provided dependencies.

    Args:
        args: Worker health probe configuration arguments

    Returns:
        HealthProbe instance with all checkers registered
    """
    probe = HealthProbe(HealthProbeOptions())

    # Register Redis (Valkey) health checker
    await probe.register(
        HealthCheckKey(service_group=REDIS, component_id=ComponentId("valkey")),
        ValkeyHealthChecker(client=args.valkey_client, timeout=args.timeout),
    )

    # Register App Proxy Coordinator health checker
    await probe.register(
        HealthCheckKey(
            service_group=ServiceGroup("coordinator"), component_id=ComponentId("coordinator-http")
        ),
        HttpHealthChecker(
            url=args.coordinator_url.rstrip("/") + "/status",
            session=aiohttp.ClientSession(),
            timeout=args.timeout,
        ),
    )

    return probe
