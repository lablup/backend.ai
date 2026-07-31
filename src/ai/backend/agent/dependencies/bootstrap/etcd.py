from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.health_checker import ServiceHealthChecker
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker


class AgentEtcdDependency(DependencyProvider[AgentUnifiedConfig, AsyncEtcd]):
    """Provides etcd client for agent using loaded config.

    Initializes etcd client from agent config, matching the behavior
    in server.py's etcd_ctx() (lines 1345-1367).
    """

    @property
    @override
    def stage_name(self) -> str:
        return "etcd"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: AgentUnifiedConfig) -> AsyncIterator[AsyncEtcd]:
        """Initialize and provide etcd client.

        Args:
            setup_input: Loaded agent configuration

        Yields:
            Initialized etcd client

        Note:
            The scope_prefix_map depends on auto-detected agent identity,
            but for dependencies verify, we use the config as-is.
        """
        # Prepare credentials if configured
        etcd_credentials = None
        if setup_input.etcd.user and setup_input.etcd.password:
            etcd_credentials = {
                "user": setup_input.etcd.user,
                "password": setup_input.etcd.password,
            }

        # Build scope prefix map (same as server.py's etcd_ctx)
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
            ConfigScopes.NODE: f"nodes/agents/{setup_input.agent.id}",
        }

        # Convert config to dataclass format and initialize etcd
        etcd_config_data = setup_input.etcd.to_dataclass()
        async with AsyncEtcd(
            [addr.to_legacy() for addr in etcd_config_data.addrs],
            setup_input.etcd.namespace,
            scope_prefix_map,
            credentials=etcd_credentials,
        ) as etcd:
            yield etcd

    @override
    def gen_liveness_checker(self, resource: AsyncEtcd) -> ServiceHealthChecker:
        """Liveness — stuck etcd connection observed; restart is the recovery path."""
        return EtcdHealthChecker(etcd=resource)
