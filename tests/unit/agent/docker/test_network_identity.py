"""What a Docker agent advertises about its overlay identity at startup (BEP-1078).

The manager pre-seeds session membership straight from the published VTEP, and pairs the
cluster-network driver against the published backend. Both guards fall back to "allow" on an
absent key, so an agent that never publishes degrades silently: the pre-seed simply never
happens and the pairing check never fires. These pin the publishing itself.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import pathlib
from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any, cast
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest

import ai.backend.agent.server as agent_server
from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.docker.agent import DockerAgent, DockerKernelCreationContext
from ai.backend.agent.errors.agent import ContainerCreationError
from ai.backend.agent.network.caps import withdraw_vtep
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
    """What `_publish_network_identity` asks of the session network.

    `serving_vtep` is the endpoint sessions are actually built on, fixed when the agent started.
    The advert is about that, not about what the host happens to hold now.
    """

    def __init__(self, serving_vtep: str | None) -> None:
        self.serving_vtep = serving_vtep

    async def retry_recovery_fail_close(self) -> dict[str, str]:
        return {}


class _AgentStub:
    """The slice of DockerAgent that `_publish_network_identity` actually touches."""

    def __init__(self, vtep_ip: str | None, host_ip: str) -> None:
        self.etcd = _RecordingEtcd()
        self.id = "i-abc123"
        self._boot_id = "boot-1"
        # The run this agent id currently names. Publishing and withdrawing are both conditional
        # on it: an id restarted quickly has two processes alive at once, and either one writing
        # over the other's advert is a node that is up but invisible, or gone but advertised.
        self.etcd.puts["network/agent/i-abc123/boot"] = "boot-1"
        self._vtep_ip = vtep_ip
        self._host_ip = host_ip
        # The interface the data plane was built on. Half of the serving identity: an address that
        # moves to another NIC stays usable and stops being what this node builds with.
        self._serving_uplink = "eth-serving"
        # The refresh task, which shutdown has to stop before it can take the advert away for
        # good -- a publish already in flight would otherwise put it back.
        self._network_identity_task: asyncio.Task[None] | None = None
        # Readiness asks the privileged helper whether it is up; None means this node does not
        # use one, which is the case that needs no socket.
        self.local_config = SimpleNamespace(
            agent=SimpleNamespace(network_privnet_socket=None, backend="docker")
        )
        # Readiness also reports what recovery could not close, and retries it on this same timer.
        self._session_network = _StubSessionNetwork(vtep_ip)


async def _publish(
    stub: _AgentStub, *, still_usable: bool = True, uplink: str = "eth-serving"
) -> None:
    """Run one refresh, saying what the host would answer about the advertised address.

    The refresh asks the host afresh -- an address can go, or move to another NIC, while the
    process runs -- but only ever to decide whether to keep advertising what the serving path
    holds. ``uplink`` is the interface the host says the address is on now.
    """
    with (
        mock.patch(
            "ai.backend.agent.docker.agent.usable_vtep",
            side_effect=lambda host_ip: host_ip if still_usable else None,
        ),
        mock.patch("ai.backend.agent.docker.agent.uplink_for_ip", side_effect=lambda ip: uplink),
    ):
        await DockerAgent._publish_network_identity(cast(Any, stub))


class TestAVtepThatWentAway:
    """The refresh used to republish the address startup worked out, so a node whose link dropped
    kept a FRESH advert naming an address it no longer holds -- and the manager, reading freshness
    as liveness, placed sessions whose VXLAN source address does not exist. Recomputing it instead
    is the same mistake mirrored: the session network and the vxlan backend still hold what they
    were built with, so the node would advertise ready and then refuse the session."""

    async def test_it_is_retracted_when_the_host_stops_holding_it(self) -> None:
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        stub.etcd.puts["network/agent/i-abc123/vtep"] = "192.168.0.112"
        await _publish(stub, still_usable=False)
        assert "network/agent/i-abc123/vtep" in stub.etcd.deletes
        assert json.loads(stub.etcd.puts["network/agent/i-abc123/caps"])["vtep_ip"] is None

    async def test_an_address_that_moved_to_another_nic_is_not_advertised(self) -> None:
        """The address is still perfectly usable; it is simply not where the data plane is. The
        vxlan device goes on being created on the interface this process started with, so probing
        the new NIC and advertising it healthy builds the tunnel somewhere the traffic is not."""
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        stub.etcd.puts["network/agent/i-abc123/vtep"] = "192.168.0.112"
        await _publish(stub, still_usable=True, uplink="eth-somewhere-else")
        assert "network/agent/i-abc123/vtep" in stub.etcd.deletes
        assert json.loads(stub.etcd.puts["network/agent/i-abc123/caps"])["vtep_ip"] is None

    async def test_an_address_the_serving_path_never_took_is_not_advertised(self) -> None:
        # The node came up with its interface down, so every session it can serve is refused. The
        # interface coming back does not change that until the agent restarts, and advertising it
        # would have the manager place sessions the serving path then turns away.
        stub = _AgentStub(vtep_ip=None, host_ip="192.168.0.112")
        await _publish(stub, still_usable=True)
        assert "network/agent/i-abc123/vtep" not in stub.etcd.puts
        assert json.loads(stub.etcd.puts["network/agent/i-abc123/caps"])["vtep_ip"] is None


class TestPublishingTheVtep:
    async def test_a_usable_vtep_is_published(self) -> None:
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(stub)
        assert stub.etcd.puts["network/agent/i-abc123/vtep"] == "192.168.0.112"

    async def test_no_usable_vtep_retracts_instead_of_skipping(self) -> None:
        # Skipping would leave an address published on an earlier boot in place, and peers
        # pre-seed straight from it -- by now it may belong to a different host.
        stub = _AgentStub(vtep_ip=None, host_ip="0.0.0.0")
        stub.etcd.puts["network/agent/i-abc123/vtep"] = "10.9.9.9"  # an earlier boot's address
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

        monkeypatch.setattr("ai.backend.agent.docker.agent.probe_caps", _boom)
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(stub)
        assert stub.etcd.puts["network/agent/i-abc123/vtep"] == "192.168.0.112"


class TestTheAdvertIsWithdrawnWhenItCannotBeRenewed:
    """The capability record is what admits this node to a session, and only a freshness window
    stands between a stopped agent and a manager still choosing it. So it is written LAST -- after
    everything in the refresh that can fail -- and taken away when it cannot be renewed."""

    async def test_the_vtep_is_written_before_the_capabilities(self) -> None:
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        await _publish(stub)
        written = list(stub.etcd.puts)
        assert written.index("network/agent/i-abc123/vtep") < written.index(
            "network/agent/i-abc123/caps"
        ), "the advert landed before the things it advertises"

    async def test_a_probe_failure_takes_the_advert_away(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _boom(iface: str, **kwargs: Any) -> Any:
            raise OSError("ethtool went missing")

        monkeypatch.setattr("ai.backend.agent.docker.agent.probe_caps", _boom)
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        stub.etcd.puts["network/agent/i-abc123/caps"] = "{}"
        await _publish(stub)
        assert "network/agent/i-abc123/caps" in stub.etcd.deletes


class TestShuttingDownStopsAdvertising:
    """Deleting the advert and stopping the publisher are two things, and the order was wrong: a
    refresh already running could finish its publish after the delete and put a fresh advert back
    over a node that is shutting down -- good for the whole freshness window."""

    async def test_a_refresh_in_flight_cannot_put_the_advert_back(self) -> None:
        stub = _AgentStub(vtep_ip="192.168.0.112", host_ip="192.168.0.112")
        publishing = asyncio.Event()
        release = asyncio.Event()

        async def _slow_refresh() -> None:
            publishing.set()
            try:
                await release.wait()
            finally:
                # A publish already in flight lands whether or not the task is cancelled: the
                # write is at the store, not in this coroutine's control flow.
                stub.etcd.puts["network/agent/i-abc123/caps"] = "{}"

        stub._network_identity_task = asyncio.create_task(_slow_refresh())
        await publishing.wait()

        shutting_down = asyncio.create_task(DockerAgent._withdraw_network_identity(cast(Any, stub)))
        await asyncio.sleep(0)
        release.set()
        await shutting_down

        assert "network/agent/i-abc123/caps" not in stub.etcd.puts, (
            "a refresh in flight put the advert back after shutdown"
        )


class TestTheNodeIsAnnouncedOnlyOnceItCanServe:
    """A11c. Two things announce this node: the started event, and the heartbeat -- the manager
    marks an agent ALIVE on a heartbeat alone. Both used to begin inside `__ainit__`, while the
    backend still had work to do (the socket relay, the network plugin context, the advert that
    admits it to a cluster-network session) and before there was an RPC server to take the work
    that would follow."""

    def test_the_base_agent_neither_announces_nor_heartbeats_from_ainit(self) -> None:
        source = (
            pathlib.Path(inspect.getfile(AbstractAgent)).read_text().split("async def __ainit__")[1]
        )
        body = source.split("\n    async def ")[0]
        assert "AgentStartedEvent" not in body, (
            "the node is announced while its backend is still starting"
        )
        assert "_local_cron.start()" not in body, (
            "the heartbeat starts while its backend is still starting, and a heartbeat alone"
            " marks the node ALIVE"
        )

    def test_start_serving_does_both(self) -> None:
        source = inspect.getsource(AbstractAgent.start_serving)
        assert "_local_cron.start()" in source
        assert "AgentStartedEvent" in source

    async def test_announcing_before_the_transport_serves_is_refused(self) -> None:
        """Registering RPC handlers is not serving: the transport is entered later still, with an
        HTTP listener set up in between. Making this raise means the ordering fails loudly rather
        than depending on a reader keeping it true."""
        server = object.__new__(agent_server.AgentRPCServer)
        server._transport_entered = False
        server.runtime = MagicMock(start_serving=AsyncMock(), stop_serving=AsyncMock())

        with pytest.raises(RuntimeError, match="before its RPC transport is serving"):
            await server.start_serving()

        server.runtime.start_serving.assert_not_awaited()

    async def test_it_announces_once_the_transport_is_serving(self) -> None:
        server = object.__new__(agent_server.AgentRPCServer)
        server._transport_entered = False
        server.runtime = MagicMock(start_serving=AsyncMock(), stop_serving=AsyncMock())
        server.rpc_server = MagicMock(__aenter__=AsyncMock())

        await server.__aenter__()
        await server.start_serving()

        server.runtime.start_serving.assert_awaited_once()

    async def test_stopping_takes_the_announcement_back(self) -> None:
        # `aobject.new` does not call cleanup when `__ainit__` raises, and a failure after the
        # transport is entered unwinds without it either.
        server = object.__new__(agent_server.AgentRPCServer)
        server._transport_entered = True
        server.runtime = MagicMock(start_serving=AsyncMock(), stop_serving=AsyncMock())

        await server.stop_serving()

        server.runtime.stop_serving.assert_awaited_once()
        with pytest.raises(RuntimeError):
            await server.start_serving()


class TestAContainerThatIsUpWhenSomethingFails:
    """A11g. The container is created and started, and only then is the session network attached.
    Everything from creation onwards has to carry the container's id out with it: a plain
    exception reached the agent's handler as "kernel failed" with no id, `destroy_kernel` had
    nothing to act on, and the container went on running with its kernel already gone from the
    registry."""

    def _context(self) -> Any:
        ctx = object.__new__(DockerKernelCreationContext)
        ctx._session_networked = True
        ctx.internal_data = {}
        ctx.computers = {}
        return ctx

    async def test_a_session_network_attach_failure_names_the_container(self) -> None:
        ctx = self._context()

        async def _refuses(container: Any, cid: str, cluster_info: Any) -> None:
            raise RuntimeError("the privnet refused this session")

        ctx._attach_session_network = _refuses

        with pytest.raises(RuntimeError, match="privnet refused"):
            await ctx._provision_started_container(
                MagicMock(), MagicMock(), "cid-1", cast(Any, {}), MagicMock(allocations={})
            )

    async def test_an_additional_network_failure_names_the_container(self) -> None:
        ctx = self._context()
        ctx._session_networked = False

        async def _refuses(docker: Any, container: Any, names: Any) -> None:
            raise RuntimeError("that network does not exist")

        ctx._attach_additional_networks = _refuses

        with pytest.raises(RuntimeError, match="does not exist"):
            await ctx._provision_started_container(
                MagicMock(), MagicMock(), "cid-1", cast(Any, {}), MagicMock(allocations={})
            )

    async def test_the_caller_turns_those_into_a_named_container_failure(self) -> None:
        """The wrapper is what carries the id out, so the handler that destroys the kernel has
        something to destroy. Driven rather than read: the value of this is that a failure
        ARRIVES named, not that the source says so."""
        ctx = self._context()

        async def _refuses(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("the privnet refused this session")

        ctx._provision_started_container = _refuses
        caught: ContainerCreationError | None = None
        try:
            await DockerKernelCreationContext._provision_or_name_the_container(
                cast(Any, ctx), MagicMock(), MagicMock(), "cid-1", cast(Any, {}), MagicMock()
            )
        except ContainerCreationError as e:
            caught = e

        assert caught is not None
        assert caught.container_id == "cid-1"


class TestWithdrawingTheVtep:
    async def test_it_deletes_the_expected_key(self) -> None:
        etcd = _RecordingEtcd()
        etcd.puts["network/agent/i-abc123/vtep"] = "10.9.9.9"
        await withdraw_vtep(cast(AbstractKVStore, etcd), "i-abc123")
        assert etcd.deletes == ["network/agent/i-abc123/vtep"]
