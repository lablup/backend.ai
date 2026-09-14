from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.health_checker import HealthProbe
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.dependencies.infrastructure.redis import StorageProxyValkeyClients

from .health_probe import HealthProbeInput, HealthProbeProvider
from .service_discovery import (
    ServiceDiscoveryInput,
    ServiceDiscoveryProvider,
    ServiceDiscoveryResources,
)


@dataclass
class SystemComposerInput:
    """Input for System composer."""

    local_config: StorageProxyUnifiedConfig
    etcd: AsyncEtcd
    redis_config: RedisConfig
    valkey: StorageProxyValkeyClients
    event_producer: EventProducer


@dataclass
class SystemResources:
    """All system resources for storage proxy."""

    health_probe: HealthProbe
    service_discovery: ServiceDiscoveryResources


class SystemComposer(DependencyComposer[SystemComposerInput, SystemResources]):
    """Composer for system layer dependencies."""

    @property
    @override
    def stage_name(self) -> str:
        return "system"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: SystemComposerInput,
    ) -> AsyncIterator[SystemResources]:
        """Compose all system dependencies."""
        health_probe = await stack.enter_dependency(
            HealthProbeProvider(),
            HealthProbeInput(etcd=setup_input.etcd, valkey=setup_input.valkey),
        )
        service_discovery = await stack.enter_dependency(
            ServiceDiscoveryProvider(),
            ServiceDiscoveryInput(
                local_config=setup_input.local_config,
                etcd=setup_input.etcd,
                redis_config=setup_input.redis_config,
                event_producer=setup_input.event_producer,
            ),
        )

        yield SystemResources(
            health_probe=health_probe,
            service_discovery=service_discovery,
        )
