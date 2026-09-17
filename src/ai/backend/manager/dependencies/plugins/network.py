from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import Any, override

from ai.backend.common.etcd import ConfigScopes
from ai.backend.common.network.keys import cluster_driver_key
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.plugin.network import NetworkPluginContext

from .base import PluginDependency, PluginsInput

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class NetworkPluginDependency(PluginDependency[NetworkPluginContext]):
    """Provides NetworkPluginContext lifecycle management."""

    @property
    @override
    def stage_name(self) -> str:
        return "network-plugin"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: PluginsInput) -> AsyncIterator[NetworkPluginContext]:
        """Initialize and provide a NetworkPluginContext.

        Args:
            setup_input: Plugins input containing etcd and config

        Yields:
            Initialized NetworkPluginContext
        """
        ctx = NetworkPluginContext(setup_input.etcd, setup_input.local_config)
        await ctx.init(
            context=setup_input.init_context,
            allowlist=setup_input.allowed_plugins,
            blocklist=setup_input.disabled_plugins,
        )
        log.info("NetworkPluginContext initialized with plugins: {}", list(ctx.plugins.keys()))
        driver = cluster_driver_of(setup_input.local_config)
        # Published, not merely configured: the agents decide from it whether to run their
        # privileged network helper at all, and the driver lives in this process's own config.
        await setup_input.etcd.put(cluster_driver_key(), driver, scope=ConfigScopes.GLOBAL)
        log.info("cluster-network driver published: {}", driver)
        try:
            yield ctx
        finally:
            await ctx.cleanup()


def cluster_driver_of(local_config: Mapping[str, Any]) -> str:
    """The driver multi-node sessions are placed with, as the launcher will read it.

    The dumped config carries aliases (``inter-container``, ``default-driver``); an unset value is
    the schema's default, ``overlay``.
    """
    network = local_config.get("network") or {}
    inter = network.get("inter-container") or network.get("inter_container") or {}
    return str(inter.get("default-driver") or inter.get("default_driver") or "overlay")
