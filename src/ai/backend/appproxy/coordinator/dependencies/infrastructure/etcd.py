from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.appproxy.coordinator.errors import MissingTraefikConfigError
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.etcd import ConfigScopes
from ai.backend.common.health_checker import ServiceHealthChecker
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker


class EtcdProvider(DependencyProvider[ServerConfig, TraefikEtcd | None]):
    """Provider for Traefik etcd connection (optional)."""

    @property
    @override
    def stage_name(self) -> str:
        return "etcd"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: ServerConfig) -> AsyncIterator[TraefikEtcd | None]:
        """Create and provide Traefik etcd connection if enabled."""
        if setup_input.proxy_coordinator.enable_traefik:
            traefik_config = setup_input.proxy_coordinator.traefik
            if not traefik_config:
                raise MissingTraefikConfigError(
                    "Traefik is enabled but traefik configuration is missing."
                )

            creds: dict[str, str] | None = None
            if traefik_config.etcd.password:
                creds = {"password": traefik_config.etcd.password}

            async with TraefikEtcd(
                [addr.to_legacy() for addr in traefik_config.etcd.addrs],
                traefik_config.etcd.namespace,
                {ConfigScopes.GLOBAL: ""},
                credentials=creds,
            ) as traefik_etcd:
                yield traefik_etcd
        else:
            yield None

    @override
    def gen_liveness_checker(self, resource: TraefikEtcd | None) -> ServiceHealthChecker | None:
        """Liveness — stuck etcd connection observed; restart is the recovery path."""
        if resource is None:
            return None
        return EtcdHealthChecker(etcd=resource)
