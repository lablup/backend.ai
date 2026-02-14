from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookResult, HookResults
from ai.backend.manager.dependencies.plugins.base import PluginsInput
from ai.backend.manager.dependencies.plugins.hook import HookPluginDependency


def _make_plugins_input() -> PluginsInput:
    return PluginsInput(
        etcd=MagicMock(),
        local_config={"key": "value"},
        allowed_plugins={"plugin_a"},
        disabled_plugins={"plugin_b"},
        init_context=MagicMock(),
    )


class TestHookPluginDependency:
    def test_stage_name(self) -> None:
        dep = HookPluginDependency()
        assert dep.stage_name == "hook-plugin"

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.plugins.hook.HookPluginContext")
    async def test_provide_initializes_and_dispatches_activate(
        self, mock_ctx_class: MagicMock
    ) -> None:
        plugins_input = _make_plugins_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {"hook_plugin": MagicMock()}
        mock_ctx.dispatch = AsyncMock(
            return_value=HookResult(status=PASSED, src_plugin=["hook_plugin"])
        )
        mock_ctx_class.return_value = mock_ctx

        dep = HookPluginDependency()

        async with dep.provide(plugins_input) as ctx:
            assert ctx is mock_ctx
            mock_ctx.init.assert_called_once_with(
                context=plugins_input.init_context,
                allowlist=plugins_input.allowed_plugins,
                blocklist=plugins_input.disabled_plugins,
            )
            mock_ctx.dispatch.assert_called_once_with(
                "ACTIVATE_MANAGER",
                (),
                return_when=ALL_COMPLETED,
            )

        mock_ctx.cleanup.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.plugins.hook.HookPluginContext")
    async def test_raises_on_activate_failure(self, mock_ctx_class: MagicMock) -> None:
        plugins_input = _make_plugins_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.dispatch = AsyncMock(
            return_value=HookResult(status=HookResults.REJECTED, reason="denied")
        )
        mock_ctx_class.return_value = mock_ctx

        dep = HookPluginDependency()

        with pytest.raises(RuntimeError, match="Could not activate the manager instance"):
            async with dep.provide(plugins_input):
                pass

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.plugins.hook.HookPluginContext")
    async def test_cleanup_on_exception(self, mock_ctx_class: MagicMock) -> None:
        plugins_input = _make_plugins_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {}
        mock_ctx.dispatch = AsyncMock(return_value=HookResult(status=PASSED))
        mock_ctx_class.return_value = mock_ctx

        dep = HookPluginDependency()

        with pytest.raises(RuntimeError):
            async with dep.provide(plugins_input) as ctx:
                assert ctx is mock_ctx
                raise RuntimeError("Test error")

        mock_ctx.cleanup.assert_called_once()
