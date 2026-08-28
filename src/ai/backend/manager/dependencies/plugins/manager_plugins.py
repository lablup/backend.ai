from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.plugins.loader import ManagerPluginLoader
from ai.backend.manager.plugins.plugins import ManagerPlugins

from .base import PluginDependency, PluginsInput


class ManagerPluginsDependency(PluginDependency[ManagerPlugins]):
    """Loads every manager plugin once, at startup.

    The plugins hold no resource, so there is nothing to tear down afterwards.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "manager-plugins"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: PluginsInput) -> AsyncIterator[ManagerPlugins]:
        """Discover and build the manager plugins.

        Args:
            setup_input: Plugins input containing etcd and config

        Yields:
            The loaded ManagerPlugins

        Raises:
            ConfigurationError: If more than one authentication plugin is discovered
        """
        loader = ManagerPluginLoader(
            setup_input.plugins_config,
            allowlist=setup_input.allowed_plugins,
            blocklist=setup_input.disabled_plugins,
        )
        yield loader.load()
