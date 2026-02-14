from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.dependencies.plugins.base import PluginsInput
from ai.backend.manager.dependencies.plugins.composer import PluginsComposer, PluginsResources


def _make_plugins_input() -> PluginsInput:
    return PluginsInput(
        etcd=MagicMock(),
        local_config={"key": "value"},
        allowed_plugins={"plugin_a"},
        disabled_plugins={"plugin_b"},
        init_context=MagicMock(),
    )


class TestPluginsComposer:
    def test_stage_name(self) -> None:
        composer = PluginsComposer()
        assert composer.stage_name == "plugins"

    @pytest.mark.asyncio
    async def test_compose_all_plugins(self) -> None:
        plugins_input = _make_plugins_input()
        mock_network = MagicMock(name="network_ctx")
        mock_hook = MagicMock(name="hook_ctx")
        mock_event = MagicMock(name="event_ctx")
        mock_error = MagicMock(name="error_ctx")
        mock_stats = MagicMock(name="stats_ctx")

        mock_stack = MagicMock()
        mock_stack.enter_dependency = AsyncMock(
            side_effect=[mock_network, mock_hook, mock_event, mock_error, mock_stats]
        )

        composer = PluginsComposer()

        async with composer.compose(mock_stack, plugins_input) as resources:
            assert isinstance(resources, PluginsResources)
            assert resources.network_plugin_ctx is mock_network
            assert resources.hook_plugin_ctx is mock_hook
            assert resources.event_dispatcher_plugin_ctx is mock_event
            assert resources.error_monitor is mock_error
            assert resources.stats_monitor is mock_stats

        assert mock_stack.enter_dependency.call_count == 5

    @pytest.mark.asyncio
    async def test_compose_preserves_initialization_order(self) -> None:
        """Verify plugins are initialized in the correct order."""
        plugins_input = _make_plugins_input()
        call_order: list[str] = []

        async def track_dependency(provider: object, _input: object) -> MagicMock:
            call_order.append(type(provider).__name__)
            return MagicMock()

        mock_stack = MagicMock()
        mock_stack.enter_dependency = AsyncMock(side_effect=track_dependency)

        composer = PluginsComposer()

        async with composer.compose(mock_stack, plugins_input):
            pass

        assert call_order == [
            "NetworkPluginDependency",
            "HookPluginDependency",
            "EventDispatcherPluginDependency",
            "ErrorMonitorDependency",
            "StatsMonitorDependency",
        ]
