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
    ETCD,
    REDIS,
    ComponentId,
    HealthCheckKey,
    ServiceGroup,
)

from .hive_router import HiveRouterHealthChecker

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.client import AbstractValkeyClient


@dataclass
class WebHealthProbeArgs:
    valkey_client: AbstractValkeyClient
    etcd: AsyncEtcd
    manager_api_url: str
    hive_router_url: str
    timeout: float = 5.0


async def create_health_probe(args: WebHealthProbeArgs) -> HealthProbe:
    """
    Create and configure a HealthProbe for the Web Server component.

    This function creates a HealthProbe instance and registers health checkers
    based on the provided dependencies.

    Args:
        args: Web health probe configuration arguments

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

    # Register Manager API health checker
    await probe.register(
        HealthCheckKey(
            service_group=ServiceGroup("manager-api"), component_id=ComponentId("manager-api-http")
        ),
        HttpHealthChecker(
            url=args.manager_api_url.rstrip("/") + "/config",
            session=aiohttp.ClientSession(),
            timeout=args.timeout,
        ),
    )

    # Register Hive Router health checker
    await probe.register(
        HealthCheckKey(
            service_group=ServiceGroup("hive-router"),
            component_id=ComponentId("hive-router-http"),
        ),
        HiveRouterHealthChecker(
            url=args.hive_router_url,
            session=aiohttp.ClientSession(),
            timeout=args.timeout,
        ),
    )

    return probe
