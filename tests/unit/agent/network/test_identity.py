"""What a node advertises about its overlay identity, and when it takes it back (BEP-1078).

The manager pre-seeds session membership straight from the published VTEP and admits a node to a
cluster-network session on its capability record. Both guards fall back to "allow" on an absent
key, so an agent that never publishes degrades silently. These pin the publishing itself, for
every backend that takes part in the data plane.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from typing import Any, cast
from unittest import mock

import pytest

from ai.backend.agent.network.caps import withdraw_vtep
from ai.backend.agent.network.identity import NetworkIdentity
from ai.backend.common.etcd import AbstractKVStore


class _RecordingEtcd:
    """Records puts and deletes so a test can tell "published" from "retracted"."""

    def __init__(self) -> None:
        self.puts: dict[str, str] = {}
        self.deletes: list[str] = []

    async def compare_and_put(
        self,
        key: str,
        val: str,
        *,
        expected: str | None,
        guards: Mapping[str, str | None],
        **kwargs: Any,
    ) -> bool:
        """The store's own compare-and-swap, modelled because it is the fence being tested.

        The target must hold ``expected`` (absent when that is None) AND every guard must hold
        exactly what it is given (absent when that is None). All of it or none of it.
        """
        if self.puts.get(key) != expected:
            return False
        for guard_key, guard_val in guards.items():
            if self.puts.get(guard_key) != guard_val:
                return False
        self.puts[key] = val
        return True

    async def compare_and_delete(
        self, key: str, expected: str, *, guards: Mapping[str, str | None], **kwargs: Any
    ) -> bool:
        if self.puts.get(key) != expected:
            return False
        for guard_key, guard_val in guards.items():
            if self.puts.get(guard_key) != guard_val:
                return False
        self.puts.pop(key, None)
        self.deletes.append(key)
        return True

    async def get(self, key: str, **kwargs: Any) -> str | None:
        return self.puts.get(key)

    async def put(self, key: str, val: str, **kwargs: Any) -> None:
        self.puts[key] = val

    async def delete(self, key: str, **kwargs: Any) -> None:
        self.deletes.append(key)
        self.puts.pop(key, None)


class _StubSessionNetwork:
    """What `NetworkIdentity.publish` asks of the session network.

    `serving_vtep` is the endpoint sessions are actually built on, fixed when the agent started.
    The advert is about that, not about what the host happens to hold now.
    """

    def __init__(self, serving_vtep: str | None) -> None:
        self.serving_vtep = serving_vtep

    async def retry_recovery_fail_close(self) -> dict[str, str]:
        return {}


def _identity(vtep_ip: str | None, host_ip: str) -> tuple[NetworkIdentity, _RecordingEtcd]:
    etcd = _RecordingEtcd()
    # The run this agent id currently names. Publishing and withdrawing are both conditional on
    # it: an id restarted quickly has two processes alive at once, and either one writing over
    # the other's advert is a node that is up but invisible, or gone but advertised.
    etcd.puts["network/agent/i-abc123/boot"] = "boot-1"
    identity = NetworkIdentity(
        cast(AbstractKVStore, etcd),
        agent_id="i-abc123",
        backend="docker",
        boot_id="boot-1",
        session_network=cast(Any, _StubSessionNetwork(vtep_ip)),
        host_ip=host_ip,
        # The interface the data plane was built on. Half of the serving identity: an address
        # that moves to another NIC stays usable and stops being what this node builds with.
        serving_uplink="eth-serving",
        privnet_socket=None,
        vtep_ip=vtep_ip,
    )
    return identity, etcd


async def _publish(
    identity: NetworkIdentity, *, still_usable: bool = True, uplink: str = "eth-serving"
) -> None:
    """Run one refresh, saying what the host would answer about the advertised address.

    The refresh asks the host afresh -- an address can go, or move to another NIC, while the
    process runs -- but only ever to decide whether to keep advertising what the serving path
    holds. ``uplink`` is the interface the host says the address is on now.
    """
    with (
        mock.patch(
            "ai.backend.agent.network.identity.usable_vtep",
            side_effect=lambda host_ip: host_ip if still_usable else None,
        ),
        mock.patch(
            "ai.backend.agent.network.identity.uplink_for_ip", side_effect=lambda ip: uplink
        ),
    ):
        await identity.publish()


class TestAVtepThatWentAway:
    """The refresh used to republish the address startup worked out, so a node whose link dropped
    kept a FRESH advert naming an address it no longer holds -- and the manager, reading freshness
    as liveness, placed sessions whose VXLAN source address does not exist. Recomputing it instead
    is the same mistake mirrored: the session network and the vxlan backend still hold what they
    were built with, so the node would advertise ready and then refuse the session."""

    async def test_it_is_retracted_when_the_host_stops_holding_it(self) -> None:
        identity, etcd = _identity(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        etcd.puts["network/agent/i-abc123/vtep"] = "192.168.0.112"
        await _publish(identity, still_usable=False)
        assert "network/agent/i-abc123/vtep" in etcd.deletes
        assert json.loads(etcd.puts["network/agent/i-abc123/caps"])["vtep_ip"] is None

    async def test_an_address_that_moved_to_another_nic_is_not_advertised(self) -> None:
        """The address is still perfectly usable; it is simply not where the data plane is. The
        vxlan device goes on being created on the interface this process started with, so probing
        the new NIC and advertising it healthy builds the tunnel somewhere the traffic is not."""
        identity, etcd = _identity(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        etcd.puts["network/agent/i-abc123/vtep"] = "192.168.0.112"
        await _publish(identity, still_usable=True, uplink="eth-somewhere-else")
        assert "network/agent/i-abc123/vtep" in etcd.deletes
        assert json.loads(etcd.puts["network/agent/i-abc123/caps"])["vtep_ip"] is None

    async def test_an_address_the_serving_path_never_took_is_not_advertised(self) -> None:
        # The node came up with its interface down, so every session it can serve is refused. The
        # interface coming back does not change that until the agent restarts, and advertising it
        # would have the manager place sessions the serving path then turns away.
        identity, etcd = _identity(vtep_ip=None, host_ip="192.168.0.112")
        await _publish(identity, still_usable=True)
        assert "network/agent/i-abc123/vtep" not in etcd.puts
        assert json.loads(etcd.puts["network/agent/i-abc123/caps"])["vtep_ip"] is None


class TestPublishingTheVtep:
    async def test_a_usable_vtep_is_published(self) -> None:
        identity, etcd = _identity(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(identity)
        assert etcd.puts["network/agent/i-abc123/vtep"] == "192.168.0.112"

    async def test_no_usable_vtep_retracts_instead_of_skipping(self) -> None:
        # Skipping would leave an address published on an earlier boot in place, and peers
        # pre-seed straight from it -- by now it may belong to a different host.
        identity, etcd = _identity(vtep_ip=None, host_ip="0.0.0.0")
        etcd.puts["network/agent/i-abc123/vtep"] = "10.9.9.9"  # an earlier boot's address
        await _publish(identity, still_usable=False)
        assert "network/agent/i-abc123/vtep" not in etcd.puts
        assert "network/agent/i-abc123/vtep" in etcd.deletes

    async def test_capabilities_are_published_alongside(self) -> None:
        identity, etcd = _identity(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(identity)
        assert "network/agent/i-abc123/caps" in etcd.puts
        # The runtime, the tunnel endpoint and the time, in the SAME value as the capabilities:
        # the manager cannot otherwise tell an advert this boot made from one an earlier boot on a
        # different runtime left behind.
        published = json.loads(etcd.puts["network/agent/i-abc123/caps"])
        assert published["backend"] == "docker"
        assert published["boot_id"] == "boot-1"
        assert published["vtep_ip"] == "192.168.0.112"
        assert isinstance(published["updated_at"], float)

    async def test_a_capability_probe_failure_does_not_block_the_vtep(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The caps key is a diagnostic; the VTEP is load-bearing. Describing the uplink must not
        # be able to stop the agent from advertising where its peers can reach it.
        async def _boom(iface: str, **kwargs: Any) -> Any:
            raise OSError("ethtool went missing")

        monkeypatch.setattr("ai.backend.agent.network.identity.probe_caps", _boom)
        identity, etcd = _identity(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(identity)
        assert etcd.puts["network/agent/i-abc123/vtep"] == "192.168.0.112"


class TestTheAdvertIsWithdrawnWhenItCannotBeRenewed:
    """The capability record is what admits this node to a session, and only a freshness window
    stands between a stopped agent and a manager still choosing it. So it is written LAST -- after
    everything in the refresh that can fail -- and taken away when it cannot be renewed."""

    async def test_the_vtep_is_written_before_the_capabilities(self) -> None:
        identity, etcd = _identity(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(identity)
        written = list(etcd.puts)
        assert written.index("network/agent/i-abc123/vtep") < written.index(
            "network/agent/i-abc123/caps"
        ), "the advert landed before the things it advertises"

    async def test_a_probe_failure_takes_the_advert_away(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _boom(iface: str, **kwargs: Any) -> Any:
            raise OSError("ethtool went missing")

        monkeypatch.setattr("ai.backend.agent.network.identity.probe_caps", _boom)
        identity, etcd = _identity(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        etcd.puts["network/agent/i-abc123/caps"] = "{}"
        await _publish(identity)
        assert "network/agent/i-abc123/caps" in etcd.deletes


class TestShuttingDownStopsAdvertising:
    """Deleting the advert and stopping the publisher are two things, and the order was wrong: a
    refresh already running could finish its publish after the delete and put a fresh advert back
    over a node that is shutting down -- good for the whole freshness window."""

    async def test_a_refresh_in_flight_cannot_put_the_advert_back(self) -> None:
        identity, etcd = _identity(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        publishing = asyncio.Event()
        release = asyncio.Event()

        async def _slow_refresh() -> None:
            publishing.set()
            try:
                await release.wait()
            finally:
                # A publish already in flight lands whether or not the task is cancelled: the
                # write is at the store, not in this coroutine's control flow.
                etcd.puts["network/agent/i-abc123/caps"] = "{}"

        identity._refresh_task = asyncio.create_task(_slow_refresh())
        await publishing.wait()

        shutting_down = asyncio.create_task(identity.stop())
        await asyncio.sleep(0)
        release.set()
        await shutting_down

        assert "network/agent/i-abc123/caps" not in etcd.puts, (
            "a refresh in flight put the advert back after shutdown"
        )


class TestWithdrawingTheVtep:
    async def test_it_deletes_the_expected_key(self) -> None:
        etcd = _RecordingEtcd()
        etcd.puts["network/agent/i-abc123/vtep"] = "10.9.9.9"
        await withdraw_vtep(cast(AbstractKVStore, etcd), "i-abc123")
        assert etcd.deletes == ["network/agent/i-abc123/vtep"]
