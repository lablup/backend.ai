from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.plugin.network import NetworkPluginContext

from .base import PluginsInput
from .event_dispatcher import EventDispatcherPluginDependency
from .hook import HookPluginDependency
from .network import NetworkPluginDependency


@dataclass
class PluginsResources:
    """Container for all plugin context resources."""

    hook_plugin_ctx: HookPluginContext
    network_plugin_ctx: NetworkPluginContext
    event_dispatcher_plugin_ctx: EventDispatcherPluginContext


class PluginsComposer(DependencyComposer[PluginsInput, PluginsResources]):
    """Composes plugin context dependencies (network, hook, event dispatcher).

    Monitoring plugins (error_monitor, stats_monitor) are initialized separately
    in MonitoringComposer (after DomainComposer) because they require
    error_log_repository which is only available post-Domain stage.

    Initializes plugin contexts in the following order:
    1. NetworkPluginContext
    2. HookPluginContext (dispatches ACTIVATE_MANAGER)
    3. EventDispatcherPluginContext
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

        yield PluginsResources(
            hook_plugin_ctx=hook_plugin_ctx,
            network_plugin_ctx=network_plugin_ctx,
            event_dispatcher_plugin_ctx=event_dispatcher_plugin_ctx,
        )
