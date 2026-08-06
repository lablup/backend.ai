"""Cluster DNS wiring in ContainerdSessionNetwork (BEP-1062).

These cover the agent-side lifecycle glue — deriving the LOCAL gateway and starting/stopping the
per-session resolver. The resolver's own resolve/forward behaviour is tested in
tests/unit/agent/network/privnet/test_resolver.py; the name source in test_coordinator.py.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

import ai.backend.agent.containerd.session_network as session_network_mod
from ai.backend.agent.containerd.session_network import ContainerdSessionNetwork


def _network(subnet: str | None) -> ContainerdSessionNetwork:
    async def _privnet_local_subnet(_session_id: str) -> str | None:
        return subnet

    return ContainerdSessionNetwork(
        cast(Any, Mock()),
        agent_id="a1",
        host_ip="192.168.0.10",
        runtime=cast(Any, Mock()),
        cni_runner=cast(Any, Mock()),
        backends={},
        privnet_local_subnet=_privnet_local_subnet,
    )


class _FakeDNSServer:
    """Records the address it was told to bind, without opening a socket."""

    instances: list[_FakeDNSServer] = []

    def __init__(self, resolver: Any, bind_host: str, *, port: int = 53) -> None:
        self.bind_host = bind_host
        self.port = port
        self.started = False
        self.stopped = False
        _FakeDNSServer.instances.append(self)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


@pytest.fixture(autouse=True)
def _fake_dns_server(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeDNSServer.instances = []
    monkeypatch.setattr(session_network_mod, "ClusterDNSServer", _FakeDNSServer)


class TestLocalGateway:
    async def test_returns_the_first_usable_host(self) -> None:
        net = _network("10.128.5.0/26")
        assert await net.local_gateway_of("s1") == "10.128.5.1"

    async def test_none_when_no_subnet_is_claimed(self) -> None:
        net = _network(None)
        assert await net.local_gateway_of("s1") is None

    async def test_none_on_an_unparseable_subnet(self) -> None:
        net = _network("not-a-subnet")
        assert await net.local_gateway_of("s1") is None


class TestClusterDNSLifecycle:
    async def test_start_binds_the_session_gateway(self) -> None:
        net = _network("10.128.5.0/26")
        await net._start_cluster_dns("s1", cast(Any, Mock()))
        assert len(_FakeDNSServer.instances) == 1
        server = _FakeDNSServer.instances[0]
        assert server.bind_host == "10.128.5.1"
        assert server.started

    async def test_start_is_skipped_without_a_gateway(self) -> None:
        # Best-effort: no gateway -> no server, no raise (container still has /etc/hosts + upstream).
        net = _network(None)
        await net._start_cluster_dns("s1", cast(Any, Mock()))
        assert _FakeDNSServer.instances == []

    async def test_stop_stops_and_forgets_the_server(self) -> None:
        net = _network("10.128.5.0/26")
        await net._start_cluster_dns("s1", cast(Any, Mock()))
        server = _FakeDNSServer.instances[0]
        await net._stop_cluster_dns("s1")
        assert server.stopped
        # A second stop is a no-op (already forgotten), not an error.
        await net._stop_cluster_dns("s1")

    async def test_a_failed_bind_is_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        net = _network("10.128.5.0/26")
        failing = Mock()
        failing.start = AsyncMock(side_effect=OSError("address in use"))
        monkeypatch.setattr(session_network_mod, "ClusterDNSServer", lambda *a, **k: failing)
        await net._start_cluster_dns("s1", cast(Any, Mock()))  # must not raise
        # The half-started server is not registered, so teardown won't try to stop it.
        await net._stop_cluster_dns("s1")
