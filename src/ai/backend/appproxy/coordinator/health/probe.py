from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncEngine

from ai.backend.common.health.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.health.probe import HealthProbe, HealthProbeOptions
from ai.backend.common.health.types import (
    DATABASE,
    REDIS,
    ComponentId,
    HealthCheckKey,
)

from .database import DatabaseHealthChecker

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.client import AbstractValkeyClient


@dataclass
class CoordinatorHealthProbeArgs:
    db: AsyncEngine
    valkey_client: AbstractValkeyClient
    timeout: float = 5.0


async def create_health_probe(args: CoordinatorHealthProbeArgs) -> HealthProbe:
    """
    Create and configure a HealthProbe for the App Proxy Coordinator component.

    This function creates a HealthProbe instance and registers health checkers
    based on the provided dependencies.

    Args:
        args: Coordinator health probe configuration arguments

    Returns:
        HealthProbe instance with all checkers registered
    """
    probe = HealthProbe(HealthProbeOptions())

    # Register Database health checker
    await probe.register(
        HealthCheckKey(service_group=DATABASE, component_id=ComponentId("postgres")),
        DatabaseHealthChecker(args.db, timeout=args.timeout),
    )

    # Register Redis (Valkey) health checker
    await probe.register(
        HealthCheckKey(service_group=REDIS, component_id=ComponentId("valkey")),
        ValkeyHealthChecker(client=args.valkey_client, timeout=args.timeout),
    )

    return probe
