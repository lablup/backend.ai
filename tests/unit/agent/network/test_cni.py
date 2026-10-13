"""The CNI contract the agent speaks: netns handover, results, and which plugin a session names."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from types import SimpleNamespace
from typing import Any, cast, override
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.network.cni import (
    CniAttachment,
    CniIpConfig,
    CniRequest,
    CniResult,
    CniStatus,
    netns_path_for_pid,
    pid_of_netns_path,
)
from ai.backend.agent.plugin.cni import AbstractCniPlugin, CniPluginContext
from ai.backend.plugin.entrypoint import match_plugin_list


class TestTheNetnsHandover:
    def test_a_pid_becomes_its_proc_path(self) -> None:
        assert netns_path_for_pid(4242) == "/proc/4242/ns/net"

    def test_the_path_gives_the_pid_back(self) -> None:
        assert pid_of_netns_path("/proc/4242/ns/net") == 4242

    @pytest.mark.parametrize(
        "netns",
        ["", "/proc/0/ns/net", "/proc/self/ns/net", "/var/run/netns/x", "/proc/12/ns/net/"],
    )
    def test_any_other_form_names_no_pid(self, netns: str) -> None:
        assert pid_of_netns_path(netns) is None


class TestTheResult:
    def test_the_first_ip_is_the_primary_one(self) -> None:
        result = CniResult(
            ips=[CniIpConfig("172.30.0.5/26", gateway="172.30.0.1"), CniIpConfig("10.1.0.2/24")]
        )
        assert result.primary_ip == "172.30.0.5"

    def test_no_ip_is_no_primary(self) -> None:
        assert CniResult().primary_ip is None


class TestWhichPluginASessionNames:
    """A session's network config names its plugin in ``type``; anything else is Docker's."""

    @pytest.fixture
    def ctx(self) -> CniPluginContext:
        ctx = CniPluginContext(MagicMock(), {})
        ctx.plugins["example"] = cast(AbstractCniPlugin, MagicMock())
        return ctx

    def test_a_loaded_plugin_is_found(self, ctx: CniPluginContext) -> None:
        assert ctx.plugin_of({"type": "example", "subnet": "10.1.0.0/24"}) is ctx.plugins["example"]

    def test_a_plugin_that_is_not_loaded_is_none(self, ctx: CniPluginContext) -> None:
        assert ctx.plugin_of({"type": "calico"}) is None

    @pytest.mark.parametrize(
        "config",
        [None, {}, {"mode": "overlay", "network_name": "bai-net"}, {"type": 3}],
    )
    def test_a_config_naming_no_plugin_is_none(
        self, ctx: CniPluginContext, config: dict[str, Any] | None
    ) -> None:
        assert ctx.plugin_of(config) is None


class _Installed(AbstractCniPlugin):
    config_watch_enabled = False

    @override
    async def init(self, context: Any = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        pass

    @override
    async def add(self, request: CniRequest) -> CniResult:
        return CniResult()

    @override
    async def delete(self, request: CniRequest) -> None:
        pass

    @override
    async def status(self) -> CniStatus:
        return CniStatus()

    @override
    async def gc(self, valid: Sequence[CniAttachment]) -> None:
        pass


class TestAnInstalledPluginLoadsOnlyWhenAllowed:
    """A loaded plugin gates the heartbeat, so installing its package is not enough."""

    @pytest.fixture(autouse=True)
    def installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def scan(
            group: str, allowlist: set[str] | None = None, blocklist: set[str] | None = None
        ) -> Iterator[Any]:
            value = "example.net.cni.plugin:ExamplePlugin"
            if allowlist is None or match_plugin_list(value, allowlist):
                yield SimpleNamespace(name="ex", value=value, load=lambda: _Installed)

        monkeypatch.setattr("ai.backend.common.plugin.scan_entrypoints", scan)

    @staticmethod
    async def _loaded(allowlist: set[str] | None) -> list[str]:
        ctx = CniPluginContext(MagicMock(get_prefix=AsyncMock(return_value={})), {})
        await ctx.init(context=None, allowlist=allowlist)
        return list(ctx.plugins)

    @pytest.mark.parametrize("allowlist", [None, set()])
    async def test_one_not_named_is_not_loaded(self, allowlist: set[str] | None) -> None:
        assert await self._loaded(allowlist) == []

    async def test_one_named_by_its_package_is_loaded(self) -> None:
        assert await self._loaded({"example.net"}) == ["ex"]

    async def test_its_entry_point_name_does_not_name_it(self) -> None:
        assert await self._loaded({"ex"}) == []
