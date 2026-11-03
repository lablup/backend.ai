from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

import aiohttp

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.coordinator.clients.worker.traefik.client import TraefikWorkerClient
from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.appproxy.coordinator.dependencies.components.traefik_worker_client import (
    TraefikWorkerClientInput,
    TraefikWorkerClientProvider,
)
from ai.backend.appproxy.coordinator.dependencies.components.worker_client_pool import (
    WorkerClientPoolProvider,
)
from ai.backend.common.clients.http_client.client_pool import ClientPool
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.service_discovery.service_discovery import ServiceDiscovery


@dataclass(frozen=True)
class ComponentsInput:
    config: ServerConfig
    worker_client_timeout: aiohttp.ClientTimeout
    traefik_etcd: TraefikEtcd | None
    worker_service_discovery: ServiceDiscovery
    max_concurrent_traefik_etcd_calls: int


@dataclass(frozen=True)
class ComponentsResources:
    worker_client_pool: ClientPool
    traefik_worker_client: TraefikWorkerClient | None


class ComponentsComposer(DependencyComposer[ComponentsInput, ComponentsResources]):
    """Composes the clients the coordinator sends ingresses through."""

    @property
    @override
    def stage_name(self) -> str:
        return "components"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: ComponentsInput,
    ) -> AsyncIterator[ComponentsResources]:
        worker_client_pool = await stack.enter_dependency(
            WorkerClientPoolProvider(), setup_input.worker_client_timeout
        )
        traefik_worker_client = await stack.enter_dependency(
            TraefikWorkerClientProvider(),
            TraefikWorkerClientInput(
                config=setup_input.config,
                traefik_etcd=setup_input.traefik_etcd,
                worker_service_discovery=setup_input.worker_service_discovery,
                max_concurrent_etcd_calls=setup_input.max_concurrent_traefik_etcd_calls,
            ),
        )
        yield ComponentsResources(
            worker_client_pool=worker_client_pool,
            traefik_worker_client=traefik_worker_client,
        )
