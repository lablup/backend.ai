from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.common.config import ConfigScopes
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.types import HostPortPair

from ...config import ServerConfig


class EtcdProvider(DependencyProvider[ServerConfig, TraefikEtcd | None]):
    """Provider for Traefik etcd connection (optional)."""

    @property
    def stage_name(self) -> str:
        return "etcd"

    @asynccontextmanager
    async def provide(self, setup_input: ServerConfig) -> AsyncIterator[TraefikEtcd | None]:
        """Create and provide Traefik etcd connection if enabled."""
        if setup_input.proxy_coordinator.enable_traefik:
            traefik_config = setup_input.proxy_coordinator.traefik
            assert traefik_config

            creds: dict[str, str] | None = None
            if traefik_config.etcd.password:
                creds = {"password": traefik_config.etcd.password}

            traefik_etcd = TraefikEtcd(
                HostPortPair(traefik_config.etcd.addr.host, traefik_config.etcd.addr.port),
                traefik_config.etcd.namespace,
                {ConfigScopes.GLOBAL: ""},
                credentials=creds,
            )
            yield traefik_etcd
        else:
            yield None
