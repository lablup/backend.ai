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
        # Build scope prefix map (same as server.py's etcd_ctx)
        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
            ConfigScopes.SGROUP: f"sgroup/{setup_input.agent.legacy_sgroup_name()}",
            ConfigScopes.NODE: f"nodes/agents/{setup_input.agent.id}",
        }
        async with AsyncEtcd.create_from_config(
            setup_input.etcd.to_dataclass(), scope_prefix_map
        ) as etcd:
            yield etcd

    @override
    def gen_liveness_checker(self, resource: AsyncEtcd) -> ServiceHealthChecker:
        """Liveness — stuck etcd connection observed; restart is the recovery path."""
        return EtcdHealthChecker(etcd=resource)
