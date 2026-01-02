from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.common.config import ConfigScopes
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import ServiceHealthChecker
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker
from ai.backend.common.types import HostPortPair

from ...config import ServerConfig
from ...errors import MissingTraefikConfigError


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
            if not traefik_config:
                raise MissingTraefikConfigError(
                    "Traefik is enabled but traefik configuration is missing."
                )

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

    def gen_health_checkers(self, resource: TraefikEtcd | None) -> ServiceHealthChecker | None:
        """
        Return health checker for etcd if enabled.

        Args:
            resource: The initialized etcd client or None if not enabled

        Returns:
            Health checker for etcd if enabled, None otherwise
        """
        if resource is None:
            return None
        return EtcdHealthChecker(etcd=resource)
