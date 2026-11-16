from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.appproxy.coordinator.dependencies.system.service_discovery import (
    ServiceDiscoveryInput,
    ServiceDiscoveryProvider,
)
from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceDiscoveryLoop,
)


@dataclass
class SystemInput:
    config: ServerConfig
    sentinel_monitors: SentinelMonitorSet


@dataclass
class SystemResources:
    worker_service_discovery: ServiceDiscovery
    core_service_discovery: ServiceDiscovery
    sd_loop: ServiceDiscoveryLoop


class SystemComposer(DependencyComposer[SystemInput, SystemResources]):
    """Composes the service discovery of the coordinator."""

    @property
    @override
    def stage_name(self) -> str:
        return "system"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: SystemInput,
    ) -> AsyncIterator[SystemResources]:
        service_discovery = await stack.enter_dependency(
            ServiceDiscoveryProvider(),
            ServiceDiscoveryInput(
                config=setup_input.config,
                sentinel_monitors=setup_input.sentinel_monitors,
            ),
        )
        yield SystemResources(
            worker_service_discovery=service_discovery.worker_service_discovery,
            core_service_discovery=service_discovery.core_service_discovery,
            sd_loop=service_discovery.sd_loop,
        )
