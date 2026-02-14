from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.plugin.monitor import ManagerErrorPluginContext, ManagerStatsPluginContext
from ai.backend.manager.plugin.network import NetworkPluginContext

from .base import PluginsInput
from .event_dispatcher import EventDispatcherPluginDependency
from .hook import HookPluginDependency
from .monitoring import ErrorMonitorDependency, StatsMonitorDependency
from .network import NetworkPluginDependency


@dataclass
class PluginsResources:
    """Container for all plugin context resources."""

    hook_plugin_ctx: HookPluginContext
    network_plugin_ctx: NetworkPluginContext
    event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    error_monitor: ManagerErrorPluginContext | None = field(default=None)
    stats_monitor: ManagerStatsPluginContext | None = field(default=None)


class PluginsComposer(DependencyComposer[PluginsInput, PluginsResources]):
    """Composes all plugin context dependencies.

    Initializes plugin contexts in the following order
    (preserving the current server.py initialization order):
    1. NetworkPluginContext
    2. HookPluginContext (dispatches ACTIVATE_MANAGER)
    3. EventDispatcherPluginContext
    4. ErrorMonitorDependency (tolerates init failures)
    5. StatsMonitorDependency (tolerates init failures)
    """

    @property
    def stage_name(self) -> str:
        return "plugins"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: PluginsInput,
    ) -> AsyncIterator[PluginsResources]:
        """Compose plugin context dependencies in order.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Plugins input containing etcd and config

        Yields:
            PluginsResources containing all plugin contexts
        """
        network_plugin_ctx = await stack.enter_dependency(
            NetworkPluginDependency(),
            setup_input,
        )

        hook_plugin_ctx = await stack.enter_dependency(
            HookPluginDependency(),
            setup_input,
        )

        event_dispatcher_plugin_ctx = await stack.enter_dependency(
            EventDispatcherPluginDependency(),
            setup_input,
        )

        error_monitor = await stack.enter_dependency(
            ErrorMonitorDependency(),
            setup_input,
        )

        stats_monitor = await stack.enter_dependency(
            StatsMonitorDependency(),
            setup_input,
        )

        yield PluginsResources(
            hook_plugin_ctx=hook_plugin_ctx,
            network_plugin_ctx=network_plugin_ctx,
            event_dispatcher_plugin_ctx=event_dispatcher_plugin_ctx,
            error_monitor=error_monitor,
            stats_monitor=stats_monitor,
        )
