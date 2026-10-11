from collections.abc import AsyncIterator, Mapping
from typing import Any, cast, override
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext


class EtcdReadError(Exception):
    pass


class PluginRefusedError(Exception):
    pass


class FakeEtcd:
    """Emits a fixed number of watch events; each `get_prefix` call pops the next outcome."""

    _events: int
    _outcomes: list[Mapping[str, Any] | Exception]
    get_prefix_calls: int

    def __init__(self, events: int, outcomes: list[Mapping[str, Any] | Exception]) -> None:
        self._events = events
        self._outcomes = outcomes
        self.get_prefix_calls = 0

    async def watch_prefix(self, key_prefix: str, **kwargs: Any) -> AsyncIterator[object]:
        for _ in range(self._events):
            yield object()

    async def get_prefix(self, key_prefix: str, **kwargs: Any) -> Mapping[str, Any]:
        self.get_prefix_calls += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class RecordingPlugin(AbstractPlugin):
    applied: list[Mapping[str, Any]]
    _refuse_first: int

    def __init__(self, refuse_first: int = 0) -> None:
        super().__init__({}, {})
        self.applied = []
        self._refuse_first = refuse_first

    @override
    async def init(self, context: Any | None = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        if self._refuse_first > 0:
            self._refuse_first -= 1
            raise PluginRefusedError("bad config")
        self.applied.append(plugin_config)


def _make_ctx(etcd: FakeEtcd, plugin: AbstractPlugin) -> BasePluginContext[AbstractPlugin]:
    ctx: BasePluginContext[AbstractPlugin] = BasePluginContext(cast(AbstractKVStore, etcd), {})
    ctx.plugins["dummy"] = plugin
    return ctx


@pytest.fixture
def sleep_mock(mocker: MockerFixture) -> AsyncMock:
    return mocker.patch("ai.backend.common.plugin._config_retry_sleep", new_callable=AsyncMock)


class TestPluginConfigWatcher:
    async def test_failed_read_is_retried_and_applied_once(self, sleep_mock: AsyncMock) -> None:
        etcd = FakeEtcd(events=1, outcomes=[EtcdReadError("down"), {"a": "1"}])
        plugin = RecordingPlugin()
        ctx = _make_ctx(etcd, plugin)

        await ctx._watcher("dummy")

        assert etcd.get_prefix_calls == 2
        assert plugin.applied == [{"a": "1"}]
        sleep_mock.assert_awaited_once_with(BasePluginContext._CONFIG_RETRY_BACKOFF_SEC)

    async def test_refused_config_keeps_watcher_running(self, sleep_mock: AsyncMock) -> None:
        etcd = FakeEtcd(events=2, outcomes=[{"a": "bad"}, {"a": "good"}])
        plugin = RecordingPlugin(refuse_first=1)
        ctx = _make_ctx(etcd, plugin)

        await ctx._watcher("dummy")

        assert etcd.get_prefix_calls == 2
        assert plugin.applied == [{"a": "good"}]
        sleep_mock.assert_not_awaited()

    async def test_backoff_doubles_up_to_ceiling(self, sleep_mock: AsyncMock) -> None:
        failures = 20
        outcomes: list[Mapping[str, Any] | Exception] = [
            EtcdReadError("down") for _ in range(failures)
        ]
        etcd = FakeEtcd(events=1, outcomes=[*outcomes, {"a": "1"}])
        plugin = RecordingPlugin()
        ctx = _make_ctx(etcd, plugin)

        await ctx._watcher("dummy")

        delays = [call.args[0] for call in sleep_mock.await_args_list]
        assert len(delays) == failures
        assert delays[:4] == [0.5, 1.0, 2.0, 4.0]
        assert max(delays) == BasePluginContext._CONFIG_RETRY_CEILING_SEC
        assert delays[-1] == BasePluginContext._CONFIG_RETRY_CEILING_SEC
        assert plugin.applied == [{"a": "1"}]
