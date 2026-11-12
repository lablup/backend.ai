from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext


class TestBasePluginContextInitialization:
    @pytest.fixture
    def plugin_entry(self) -> MagicMock:
        plugin = MagicMock(spec=AbstractPlugin)
        plugin.config_watch_enabled = False
        return MagicMock(return_value=plugin)

    @pytest.fixture
    def plugin_context(
        self, mocker: MockerFixture, plugin_entry: MagicMock
    ) -> BasePluginContext[AbstractPlugin]:
        etcd = AsyncMock(spec=AbstractKVStore)
        etcd.get_prefix.return_value = {}
        healthy_plugin = MagicMock(spec=AbstractPlugin)
        healthy_plugin.config_watch_enabled = False
        mocker.patch.object(
            BasePluginContext,
            "discover_plugins",
            return_value=[
                ("failing", plugin_entry),
                ("healthy", MagicMock(return_value=healthy_plugin)),
            ],
        )
        return BasePluginContext(etcd, {})

    @pytest.mark.parametrize("failure_stage", ["constructor", "init"])
    async def test_validation_error_aborts_initialization(
        self,
        plugin_context: BasePluginContext[AbstractPlugin],
        plugin_entry: MagicMock,
        failure_stage: str,
    ) -> None:
        error = ValidationError.from_exception_data(
            "PluginConfig", [{"type": "missing", "loc": ("token_secret",), "input": {}}]
        )
        failing_call = (
            plugin_entry if failure_stage == "constructor" else plugin_entry.return_value.init
        )
        failing_call.side_effect = error

        with pytest.raises(ValidationError) as exc_info:
            await plugin_context.init()

        assert exc_info.value is error
        assert not plugin_context.plugins

    @pytest.mark.parametrize("failure_stage", ["constructor", "init"])
    async def test_other_error_skips_plugin_and_continues(
        self,
        plugin_context: BasePluginContext[AbstractPlugin],
        plugin_entry: MagicMock,
        failure_stage: str,
    ) -> None:
        failing_call = (
            plugin_entry if failure_stage == "constructor" else plugin_entry.return_value.init
        )
        failing_call.side_effect = RuntimeError("Plugin unavailable")

        await plugin_context.init()

        assert set(plugin_context.plugins) == {"healthy"}
