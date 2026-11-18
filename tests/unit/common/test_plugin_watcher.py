from unittest.mock import MagicMock, call

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext


class TestBasePluginContextWatcher:
    @pytest.fixture
    def plugin(self) -> MagicMock:
        plugin = MagicMock(spec=AbstractPlugin)
        plugin.update_plugin_config.side_effect = [
            ValidationError.from_exception_data(
                "PluginConfig", [{"type": "missing", "loc": ("token_secret",), "input": {}}]
            ),
            None,
        ]
        return plugin

    @pytest.fixture
    def plugin_context(self, plugin: MagicMock) -> BasePluginContext[AbstractPlugin]:
        etcd = MagicMock(spec=AbstractKVStore)
        etcd.watch_prefix.return_value.__aiter__.return_value = [object(), object()]
        etcd.get_prefix.side_effect = [{}, {"token_secret": "restored-secret"}]
        context: BasePluginContext[AbstractPlugin] = BasePluginContext(etcd, {})
        context.plugins["dummy"] = plugin
        return context

    async def test_validation_error_is_logged_and_next_config_is_applied(
        self,
        plugin_context: BasePluginContext[AbstractPlugin],
        plugin: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        log_exception = mocker.patch("ai.backend.common.plugin.log.exception")

        await plugin_context._watcher("dummy")

        assert plugin.update_plugin_config.await_args_list == [
            call({}),
            call({"token_secret": "restored-secret"}),
        ]
        log_exception.assert_called_once_with(
            "plugin configuration validation failed", plugin_name="dummy"
        )
