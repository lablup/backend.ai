"""What a Docker agent advertises about its overlay identity at startup (BEP-1078).

The manager pre-seeds session membership straight from the published VTEP, and pairs the
cluster-network driver against the published backend. Both guards fall back to "allow" on an
absent key, so an agent that never publishes degrades silently: the pre-seed simply never
happens and the pairing check never fires. These pin the publishing itself.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, cast
from unittest import mock

import pytest

from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.agent.network.caps import withdraw_vtep
from ai.backend.common.etcd import AbstractKVStore


class _RecordingEtcd:
    """Records puts and deletes so a test can tell "published" from "retracted"."""

    def __init__(self) -> None:
        self.puts: dict[str, str] = {}
        self.deletes: list[str] = []

    async def put(self, key: str, val: str, **kwargs: Any) -> None:
        self.puts[key] = val

    async def delete(self, key: str, **kwargs: Any) -> None:
        self.deletes.append(key)
        self.puts.pop(key, None)


class _StubSessionNetwork:
    """The one thing `_publish_network_identity` asks of the session network."""

    async def retry_recovery_fail_close(self) -> dict[str, str]:
        return {}


class _AgentStub:
    """The slice of DockerAgent that `_publish_network_identity` actually touches."""

    def __init__(self, vtep_ip: str | None, host_ip: str) -> None:
        self.etcd = _RecordingEtcd()
        self.id = "i-abc123"
        self._vtep_ip = vtep_ip
        self._host_ip = host_ip
        # Readiness asks the privileged helper whether it is up; None means this node does not
        # use one, which is the case that needs no socket.
        self.local_config = SimpleNamespace(
            agent=SimpleNamespace(network_privnet_socket=None, backend="docker")
        )
        # Readiness also reports what recovery could not close, and retries it on this same timer.
        self._session_network = _StubSessionNetwork()


async def _publish(stub: _AgentStub, *, still_usable: bool = True) -> None:
    """Run one refresh, saying whether the host still holds the advertised address.

    The refresh re-resolves the VTEP against the live host rather than republishing what startup
    worked out -- an address can go while the process runs -- so a test has to say what the host
    would answer.
    """
    with mock.patch(
        "ai.backend.agent.docker.agent.usable_vtep",
        side_effect=lambda host_ip: host_ip if still_usable else None,
    ):
        await DockerAgent._publish_network_identity(cast(Any, stub))


class TestAVtepThatWentAway:
    """The refresh used to republish the address startup worked out, so a node whose link dropped
    or whose DHCP lease changed kept a FRESH advert naming an address it no longer holds -- and
    the manager, reading freshness as liveness, placed sessions whose VXLAN source address does
    not exist."""

    async def test_it_is_retracted_when_the_host_stops_holding_it(self) -> None:
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(stub, still_usable=False)
        assert stub.etcd.deletes == ["network/agent/i-abc123/vtep"]
        assert json.loads(stub.etcd.puts["network/agent/i-abc123/caps"])["vtep_ip"] is None

    async def test_the_advert_follows_the_address_back(self) -> None:
        stub = _AgentStub(vtep_ip=None, host_ip="192.168.0.112")
        await _publish(stub, still_usable=True)
        assert stub.etcd.puts["network/agent/i-abc123/vtep"] == "192.168.0.112"
        assert json.loads(stub.etcd.puts["network/agent/i-abc123/caps"])["vtep_ip"] == (
            "192.168.0.112"
        )


class TestPublishingTheVtep:
    async def test_a_usable_vtep_is_published(self) -> None:
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(stub)
        assert stub.etcd.puts["network/agent/i-abc123/vtep"] == "192.168.0.112"

    async def test_no_usable_vtep_retracts_instead_of_skipping(self) -> None:
        # Skipping would leave an address published on an earlier boot in place, and peers
        # pre-seed straight from it -- by now it may belong to a different host.
        stub = _AgentStub(vtep_ip=None, host_ip="0.0.0.0")
        await _publish(stub, still_usable=False)
        assert "network/agent/i-abc123/vtep" not in stub.etcd.puts
        assert "network/agent/i-abc123/vtep" in stub.etcd.deletes

    async def test_capabilities_are_published_alongside(self) -> None:
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(stub)
        assert "network/agent/i-abc123/caps" in stub.etcd.puts
        # The runtime, the tunnel endpoint and the time, in the SAME value as the capabilities:
        # the manager cannot otherwise tell an advert this boot made from one an earlier boot on a
        # different runtime left behind.
        published = json.loads(stub.etcd.puts["network/agent/i-abc123/caps"])
        assert published["backend"] == "docker"
        assert published["vtep_ip"] == "192.168.0.112"
        assert isinstance(published["updated_at"], float)

    async def test_a_capability_probe_failure_does_not_block_the_vtep(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The caps key is a diagnostic; the VTEP is load-bearing. Describing the uplink must not
        # be able to stop the agent from advertising where its peers can reach it.
        async def _boom(iface: str) -> Any:
            raise OSError("ethtool went missing")

        monkeypatch.setattr("ai.backend.agent.docker.agent.probe_caps", _boom)
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(stub)
        assert stub.etcd.puts["network/agent/i-abc123/vtep"] == "192.168.0.112"


class TestWithdrawingTheVtep:
    async def test_it_deletes_the_expected_key(self) -> None:
        etcd = _RecordingEtcd()
        await withdraw_vtep(cast(AbstractKVStore, etcd), "i-abc123")
        assert etcd.deletes == ["network/agent/i-abc123/vtep"]
