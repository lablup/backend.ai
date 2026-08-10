"""Cluster DNS wiring in ContainerdSessionNetwork (BEP-1062).

These cover the agent-side lifecycle glue — binding the ephemeral loopback resolver and asking the
backend (privnet / in-process) to redirect :53 to it. The resolver's own resolve/forward behaviour
is tested in tests/unit/agent/network/privnet/test_resolver.py; the name source in
test_coordinator.py; the iptables redirect itself in test_native_attacher.py.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

import ai.backend.agent.containerd.session_network as session_network_mod
from ai.backend.agent.containerd.session_network import ContainerdSessionNetwork
from ai.backend.agent.errors.network import ClusterDNSStartError

_EPHEMERAL_PORT = 45321  # what the fake resolver reports the OS assigned


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
    """Records the bind address and reports an OS-assigned port, without opening a socket."""

    instances: list[_FakeDNSServer] = []

    def __init__(self, resolver: Any, bind_host: str, *, port: int = 53) -> None:
        self.bind_host = bind_host
        # Emulate the ephemeral-port readback: constructed with port=0, reports a real one on start.
        self.port = _EPHEMERAL_PORT if port == 0 else port
        self.started = False
        self.stopped = False
        _FakeDNSServer.instances.append(self)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


class _FakeBackend:
    """Records the :53 redirect the agent asks for (the privnet/in-process privileged step)."""

    def __init__(self) -> None:
        self.redirected: list[tuple[str, int]] = []
        self.torn_down: list[str] = []

    async def setup_dns_redirect(self, session_id: str, loopback_port: int) -> None:
        self.redirected.append((session_id, loopback_port))

    async def teardown_dns_redirect(self, session_id: str) -> None:
        self.torn_down.append(session_id)


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


def _ready(net: ContainerdSessionNetwork, session_id: str) -> _FakeBackend:
    """A session set up on this node: coordinator + resolved backend registered (post-setup)."""
    net._coordinators[session_id] = cast(Any, Mock())
    backend = _FakeBackend()
    net._session_backends[session_id] = cast(Any, backend)
    return backend


class TestClusterDNSLifecycle:
    async def test_binds_loopback_ephemeral_and_redirects(self) -> None:
        net = _network("10.128.5.0/26")
        backend = _ready(net, "s1")
        await net.ensure_cluster_dns("s1")
        assert len(_FakeDNSServer.instances) == 1
        server = _FakeDNSServer.instances[0]
        # Loopback, so it is on no real interface; ephemeral port, so it can never collide.
        assert server.bind_host == "127.0.0.1"
        assert server.started
        # ...and the backend was asked to redirect :53 to that exact port, only after the bind.
        assert backend.redirected == [("s1", _EPHEMERAL_PORT)]

    async def test_is_idempotent_across_repeated_attaches(self) -> None:
        # Every container's attach calls ensure_cluster_dns; only the first actually binds/redirects.
        net = _network("10.128.5.0/26")
        backend = _ready(net, "s1")
        await net.ensure_cluster_dns("s1")
        await net.ensure_cluster_dns("s1")
        assert len(_FakeDNSServer.instances) == 1
        assert len(backend.redirected) == 1

    async def test_skipped_without_a_coordinator(self) -> None:
        # No session set up here -> nothing to source names from, so no server, no redirect.
        net = _network("10.128.5.0/26")
        await net.ensure_cluster_dns("s1")
        assert _FakeDNSServer.instances == []

    async def test_missing_subnet_fails_loud(self) -> None:
        # After an attach the LOCAL block must exist; its absence means the redirect would no-op
        # (resolver up but unreachable), so fail the kernel rather than come up broken.
        net = _network(None)
        _ready(net, "s1")
        with pytest.raises(ClusterDNSStartError):
            await net.ensure_cluster_dns("s1")
        assert _FakeDNSServer.instances == []

    async def test_stop_stops_and_forgets_the_server(self) -> None:
        net = _network("10.128.5.0/26")
        _ready(net, "s1")
        await net.ensure_cluster_dns("s1")
        server = _FakeDNSServer.instances[0]
        await net._stop_cluster_dns("s1")
        assert server.stopped
        # A second stop is a no-op (already forgotten), not an error.
        await net._stop_cluster_dns("s1")

    async def test_a_failed_bind_fails_loud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # A bind failure must fail the kernel, not be swallowed — else the session hangs at
        # rendezvous with cluster names unresolvable and no visible cause.
        net = _network("10.128.5.0/26")
        _ready(net, "s1")
        failing = Mock()
        failing.start = AsyncMock(side_effect=OSError("address in use"))
        monkeypatch.setattr(session_network_mod, "ClusterDNSServer", lambda *a, **k: failing)
        with pytest.raises(ClusterDNSStartError):
            await net.ensure_cluster_dns("s1")
        await net._stop_cluster_dns("s1")  # the failed server is not registered

    async def test_a_failed_redirect_unwinds_and_fails_loud(self) -> None:
        # If the redirect fails after the resolver bound, the resolver is stopped and the kernel
        # fails — a resolver nothing routes to is worse than a loud error.
        net = _network("10.128.5.0/26")
        backend = _ready(net, "s1")
        backend.setup_dns_redirect = AsyncMock(side_effect=RuntimeError("privnet refused"))  # type: ignore[method-assign]
        with pytest.raises(ClusterDNSStartError):
            await net.ensure_cluster_dns("s1")
        assert _FakeDNSServer.instances[0].stopped
        # not registered, so a later teardown/stop is a no-op
        await net._stop_cluster_dns("s1")
