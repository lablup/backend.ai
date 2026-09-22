from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.network.keys import cluster_driver_key
from ai.backend.manager.dependencies.plugins.base import PluginsInput
from ai.backend.manager.dependencies.plugins.network import (
    NetworkPluginDependency,
    cluster_driver_of,
)


def _make_plugins_input() -> PluginsInput:
    etcd = MagicMock()
    etcd.put = AsyncMock()
    return PluginsInput(
        etcd=etcd,
        local_config={"key": "value"},
        allowed_plugins={"plugin_a"},
        disabled_plugins={"plugin_b"},
        init_context=MagicMock(),
    )


class TestNetworkPluginDependency:
    def test_stage_name(self) -> None:
        dep = NetworkPluginDependency()
        assert dep.stage_name == "network-plugin"

    @patch("ai.backend.manager.dependencies.plugins.network.NetworkPluginContext")
    async def test_provide_initializes_and_yields_context(self, mock_ctx_class: MagicMock) -> None:
        plugins_input = _make_plugins_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {"net_plugin": MagicMock()}
        mock_ctx_class.return_value = mock_ctx

        dep = NetworkPluginDependency()

        async with dep.provide(plugins_input) as ctx:
            assert ctx is mock_ctx
            mock_ctx_class.assert_called_once_with(plugins_input.etcd, plugins_input.local_config)
            mock_ctx.init.assert_called_once_with(
                context=plugins_input.init_context,
                allowlist=plugins_input.allowed_plugins,
                blocklist=plugins_input.disabled_plugins,
            )

        mock_ctx.cleanup.assert_called_once()

    @patch("ai.backend.manager.dependencies.plugins.network.NetworkPluginContext")
    async def test_cleanup_on_exception(self, mock_ctx_class: MagicMock) -> None:
        plugins_input = _make_plugins_input()
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {}
        mock_ctx_class.return_value = mock_ctx

        dep = NetworkPluginDependency()

        with pytest.raises(RuntimeError):
            async with dep.provide(plugins_input) as ctx:
                assert ctx is mock_ctx
                raise RuntimeError("Test error")

        mock_ctx.cleanup.assert_called_once()


class TestClusterDriverPublication:
    """The driver is this process's config, and the agents decide from it whether to run their
    privileged network helper at all -- so it is published where they can read it."""

    def test_the_dumped_config_names_the_driver_by_its_alias(self) -> None:
        assert (
            cluster_driver_of({"network": {"inter-container": {"default-driver": "cni"}}}) == "cni"
        )

    def test_an_unset_driver_is_the_schema_default(self) -> None:
        assert cluster_driver_of({"network": {"inter-container": {}}}) == "overlay"
        assert cluster_driver_of({}) == "overlay"

    @patch("ai.backend.manager.dependencies.plugins.network.NetworkPluginContext")
    async def test_provide_publishes_it(self, mock_ctx_class: MagicMock) -> None:
        plugins_input = _make_plugins_input()
        plugins_input = PluginsInput(
            etcd=plugins_input.etcd,
            local_config={"network": {"inter-container": {"default-driver": "overlay"}}},
            allowed_plugins=plugins_input.allowed_plugins,
            disabled_plugins=plugins_input.disabled_plugins,
            init_context=plugins_input.init_context,
        )
        mock_ctx = MagicMock()
        mock_ctx.init = AsyncMock()
        mock_ctx.cleanup = AsyncMock()
        mock_ctx.plugins = {}
        mock_ctx_class.return_value = mock_ctx

        async with NetworkPluginDependency().provide(plugins_input):
            pass

        put = cast(AsyncMock, plugins_input.etcd.put)
        put.assert_awaited_once()
        args, kwargs = put.call_args
        assert args[:2] == (cluster_driver_key(), "overlay")
