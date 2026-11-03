from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.coordinator.clients.worker.traefik.client import (
    TraefikWorkerClient,
    TraefikWorkerClientArgs,
)
from ai.backend.appproxy.coordinator.clients.worker.traefik.routing_config import (
    TraefikRoutingConfigFactory,
    TraefikRoutingConfigFactoryArgs,
)
from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.appproxy.coordinator.errors.config import MissingTraefikConfigError
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.service_discovery.service_discovery import ServiceDiscovery


@dataclass(frozen=True)
class TraefikWorkerClientInput:
    config: ServerConfig
    traefik_etcd: TraefikEtcd | None
    worker_service_discovery: ServiceDiscovery
    max_concurrent_etcd_calls: int


class TraefikWorkerClientProvider(
    NonMonitorableDependencyProvider[TraefikWorkerClientInput, TraefikWorkerClient | None]
):
    """The Traefik worker client, or None when the coordinator runs without Traefik etcd."""

    @property
    @override
    def stage_name(self) -> str:
        return "traefik-worker-client"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: TraefikWorkerClientInput
    ) -> AsyncIterator[TraefikWorkerClient | None]:
        if setup_input.traefik_etcd is None:
            yield None
        else:
            traefik_config = setup_input.config.proxy_coordinator.traefik
            if traefik_config is None:
                raise MissingTraefikConfigError("Traefik configuration is required")
            yield TraefikWorkerClient(
                TraefikWorkerClientArgs(
                    etcd=setup_input.traefik_etcd,
                    worker_service_discovery=setup_input.worker_service_discovery,
                    routing_config_factory=TraefikRoutingConfigFactory(
                        TraefikRoutingConfigFactoryArgs(
                            traefik_config=traefik_config,
                            secrets=setup_input.config.secrets,
                            permit_hash=setup_input.config.permit_hash,
                        )
                    ),
                    max_concurrent_etcd_calls=setup_input.max_concurrent_etcd_calls,
                )
            )
