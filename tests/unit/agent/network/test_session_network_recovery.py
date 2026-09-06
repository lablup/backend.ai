"""What a restarted agent does before it trusts anything, and what it admits it could not do.

Every field the session network holds is process memory, while the resources they name -- bridges,
veths, IPAM leases, MASQ rules, etcd members -- outlive the process. So the order matters: bring
the surviving tunnels DOWN first, because at that point no session metadata is trusted or even
readable and an open tunnel is carrying traffic nobody can account for; and whatever could not be
done has to reach readiness, or the node keeps taking overlay work it cannot serve.

These exercise the methods through the real class, on an object built with the constructor's own
defaults, so a signature change breaks them rather than passing over a stub.
"""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent.errors.network import OverlayEncryptionUnavailable
from ai.backend.agent.network.session_network import SessionNetwork
from ai.backend.agent.network.vni_registry import VniRegistry
from ai.backend.common.network.types import NetworkBackendKind, SessionNetMeta


class _Backend:
    """A network backend, as much of one as recovery touches."""

    def __init__(
        self, *, preflight_error: Exception | None = None, still_up: frozenset[str] = frozenset()
    ) -> None:
        self.preflight_error = preflight_error
        self.still_up = still_up
        self.preflight_calls = 0
        self.spared: frozenset[int] = frozenset()
        self.retry_calls = 0

    async def prepare_recovery(self, spare: Collection[int] = ()) -> None:
        self.preflight_calls += 1
        self.spared = frozenset(spare)
        if self.preflight_error is not None:
            raise self.preflight_error

    async def retry_fail_close(self) -> frozenset[str]:
        self.retry_calls += 1
        return self.still_up


def _network(**backends: _Backend) -> SessionNetwork:
    """A SessionNetwork whose only real collaborators are the backends under test."""
    return SessionNetwork(
        cast(Any, object()),
        agent_id="i-test",
        host_ip="10.0.0.1",
        cni_runner=cast(Any, None),
        locator=cast(Any, object()),
        backends=cast(Any, backends),
        # The constructor insists on exactly one source for node-local subnets; recovery does not
        # reach it, but leaving it out would be testing the constructor's guard instead.
        privnet_local_subnet=_no_local_subnet,
        vtep_ip="10.0.0.1",
    )


async def _no_local_subnet(session_id: str) -> str | None:
    return None


class TestFailCloseComesFirst:
    async def test_a_failed_preflight_is_reported_as_a_readiness_problem(self) -> None:
        backend = _Backend(preflight_error=RuntimeError("baivx4096 would not go down"))
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()  # the container listing has no real collaborator
        assert "vxlan" in network.recovery_problems()
        assert "would not go down" in network.recovery_problems()["vxlan"]

    async def test_the_preflight_runs_before_anything_is_read(self) -> None:
        # `recover` goes on to list containers, which fails here. The preflight must already have
        # happened: an open tunnel is carrying traffic while the metadata is still untrusted.
        backend = _Backend()
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()
        assert backend.preflight_calls == 1


class TestRetryIsNotTheWholePreflightAgain:
    """`prepare_recovery` brings down EVERY tunnel the backend owns and prunes every claim, which
    is right exactly once. Running it again on a timer would take down the sessions that recovered
    in between, drop their claims, and not reopen them."""

    async def test_the_retry_closes_only_what_is_still_open(self) -> None:
        backend = _Backend(preflight_error=RuntimeError("nope"))
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()
        backend.preflight_calls = 0

        await network.retry_recovery_fail_close()
        assert backend.retry_calls == 1
        assert backend.preflight_calls == 0, (
            "the retry re-ran the whole preflight; on a live node that brings down every tunnel"
            " that recovered in between and does not reopen them"
        )

    async def test_the_device_problem_clears_once_it_finally_closes(self) -> None:
        backend = _Backend(preflight_error=RuntimeError("nope"))
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()
        assert "vxlan" in network.recovery_problems()
        await network.retry_recovery_fail_close()
        assert "vxlan" not in network.recovery_problems()

    async def test_a_device_that_is_still_up_keeps_the_problem(self) -> None:
        backend = _Backend(preflight_error=RuntimeError("nope"), still_up=frozenset({"baivx4096"}))
        network = _network(vxlan=backend)
        with pytest.raises(Exception):
            await network.recover()
        remaining = await network.retry_recovery_fail_close()
        assert "baivx4096" in remaining["vxlan"]


class TestRecoveryFailuresReachReadiness:
    """A node that could not recover holds state it can neither converge nor tear down. Saying
    nothing lets it keep accepting overlay sessions."""

    async def test_a_failed_recovery_is_recorded(self) -> None:
        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        assert network.recovery_problems()["session:recovery"] == "containerd was unreachable"

    async def test_a_healthy_node_reports_nothing(self) -> None:
        network = _network(vxlan=_Backend())
        assert network.recovery_problems() == {}


class TestRecoveryIsRetriedNotJustReported:
    """A transient container-runtime or metadata error used to leave a session unmanaged -- and
    the node unable to take overlay work -- until the process restarted, because nothing ever came
    back to it."""

    async def test_the_retry_never_re_runs_the_preflight(self) -> None:
        """The preflight brings down every tunnel this node owns and prunes every claim. Right
        exactly once, before anything is trusted; on a timer it would cut the sessions that
        recovered in between -- and the resume that followed would install a SECOND coordinator
        for each of them without stopping the first."""
        backend = _Backend()
        network = _network(vxlan=backend)
        network.mark_recovery_failed("containerd was unreachable")
        backend.preflight_calls = 0
        await network.retry_recovery_fail_close()
        assert backend.preflight_calls == 0

    async def test_the_retry_attempts_the_inventory_again(self) -> None:
        # It is the inventory and resume that failed, so that is what comes back -- reported
        # again when it fails again, rather than silently cleared.
        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        await network.retry_recovery_fail_close()
        assert "session:recovery" in network.recovery_problems()

    async def test_a_node_mid_recovery_refuses_a_new_overlay_session(self) -> None:
        # Readiness tells the manager, but a request decided before it read the new capabilities
        # still arrives here, and would build a new VXLAN beside state this node can neither
        # converge nor tear down.

        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        meta = SessionNetMeta(
            session_id="s1",
            backend=NetworkBackendKind.VXLAN,
            subnet="10.128.0.0/24",
            vni=4096,
            mtu=1450,
        )
        with pytest.raises(OverlayEncryptionUnavailable):
            network._refuse_while_unrecovered(meta)

    async def test_a_node_local_session_is_not_refused(self) -> None:
        # A bridge session shares nothing with the unrecovered overlay state.

        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        meta = SessionNetMeta(
            session_id="s1",
            backend=NetworkBackendKind.BRIDGE,
            subnet="172.30.0.0/26",
            vni=None,
            mtu=1500,
        )
        network._refuse_while_unrecovered(meta)  # must not raise

    async def test_a_recovered_node_accepts_again(self) -> None:
        network = _network(vxlan=_Backend())
        meta = SessionNetMeta(
            session_id="s1",
            backend=NetworkBackendKind.VXLAN,
            subnet="10.128.0.0/24",
            vni=4096,
            mtu=1450,
        )
        network._refuse_while_unrecovered(meta)  # must not raise


class TestARetriedSessionIsFullyRecovered:
    """Resuming alone is not recovery. The tracker and the detach plans live in a separate loop in
    `recover()`, and a retry that skipped them cleared `_unresumed` -- readiness said the node was
    fine while every container of that session could give back neither its veth nor its address,
    and the last one could not start the teardown."""

    async def test_the_retry_tracks_the_containers_too(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        network = _network(vxlan=_Backend())
        resumed: list[str] = []
        tracked: list[tuple[str, str]] = []

        async def _resume(session_id: str, meta: object) -> None:
            resumed.append(session_id)

        async def _meta(session_id: str) -> object:
            return object()

        async def _inventory() -> tuple[dict[str, str], dict[str, str]]:
            return {"c1": "s1"}, {"c1": "s1"}

        async def _attachment(container_id: str, session_id: str, meta: object) -> None:
            return None

        def _track(session_id: str, container_id: str) -> None:
            tracked.append((session_id, container_id))

        monkeypatch.setattr(network, "_resume_session", _resume)
        monkeypatch.setattr(network, "_read_session_meta", _meta)
        monkeypatch.setattr(network, "_live_and_own_containers", _inventory)
        monkeypatch.setattr(network, "_recover_attachment", _attachment)
        monkeypatch.setattr(network._tracker, "track", _track)
        network.mark_recovery_failed("containerd was unreachable")

        await network.retry_recovery_fail_close()
        assert resumed == ["s1"]
        assert tracked == [("s1", "c1")], (
            "the retry resumed the session but left its containers untracked; they cannot detach"
            " and the last one cannot tear the session down"
        )
        assert network.recovery_problems() == {}


class TestTheRecoveryMarkIsNotClearedEarly:
    """The mark is what the local admission gate reads. Clearing it before the attempt succeeds
    opens a window in which a new overlay session is let onto a node that has not recovered."""

    async def test_a_failed_inventory_leaves_the_mark_in_place(self) -> None:
        network = _network(vxlan=_Backend())
        network.mark_recovery_failed("containerd was unreachable")
        await network.retry_recovery_fail_close()  # the inventory still cannot be read here
        assert "session:recovery" in network.recovery_problems()

    async def test_a_session_that_has_gone_stops_holding_the_node(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Its containers left while we were failing to resume it. Keeping the mark would hold the
        # node out of overlay service for something that ended.
        network = _network(vxlan=_Backend())

        async def _inventory() -> tuple[dict[str, str], dict[str, str]]:
            return {}, {}

        monkeypatch.setattr(network, "_live_and_own_containers", _inventory)
        network._unresumed["ghost"] = "was failing"

        await network.retry_recovery_fail_close()
        assert network.recovery_problems() == {}

    async def test_metadata_that_cannot_be_read_is_recorded_not_raised(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Reading it is part of the attempt. Outside the guard it propagated out of the retry and
        # left the pass half-done, with this session's mark already removed by the caller.
        network = _network(vxlan=_Backend())

        async def _inventory() -> tuple[dict[str, str], dict[str, str]]:
            return {"c1": "s1"}, {"c1": "s1"}

        async def _meta(session_id: str) -> object:
            raise RuntimeError("etcd was unreachable")

        monkeypatch.setattr(network, "_live_and_own_containers", _inventory)
        monkeypatch.setattr(network, "_read_session_meta", _meta)
        network._unresumed["s1"] = "was failing"

        await network.retry_recovery_fail_close()
        assert "session:s1" in network.recovery_problems()
        assert "etcd was unreachable" in network.recovery_problems()["session:s1"]


class TestWithdrawingBeforeTheMemberKeyGoes:
    """Stopping the coordinator removes this node's member key, which is the manager's signal that
    this agent has let the session go. Doing that first and then failing to withdraw leaves the
    manager believing the VNI is free while the claim, the watchdog responsibility and the
    privnet's journal record are all still here."""

    async def test_the_backend_lets_go_first(self) -> None:
        order: list[str] = []

        class _Backend2:
            async def withdraw_session_network(self, session_id: str) -> None:
                order.append("withdraw")

        class _Coordinator:
            async def stop(self, session_id: str, *, teardown_data_plane: bool = True) -> None:
                order.append(f"stop(teardown={teardown_data_plane})")

        network = _network(vxlan=_Backend())
        await network._withdraw_without_teardown(
            "s1", cast(Any, _Coordinator()), cast(Any, _Backend2())
        )
        assert order == ["withdraw", "stop(teardown=False)"]

    async def test_a_failed_withdrawal_keeps_the_member_key(self) -> None:
        stopped: list[str] = []

        class _Backend2:
            async def withdraw_session_network(self, session_id: str) -> None:
                raise RuntimeError("the journal could not confirm the release")

        class _Coordinator:
            async def stop(self, session_id: str, *, teardown_data_plane: bool = True) -> None:
                stopped.append(session_id)

        network = _network(vxlan=_Backend())
        with pytest.raises(RuntimeError):
            await network._withdraw_without_teardown(
                "s1", cast(Any, _Coordinator()), cast(Any, _Backend2())
            )
        assert stopped == [], (
            "the member key was removed anyway; the manager now believes this node let the VNI go"
        )


class TestWhatTheOtherAgentOnThisHostIsUsing:
    """D4, caller side. Sparing needs both halves: the registry says which agent holds a VNI, the
    live containers say the holder is still using it. The registry alone would let a dead agent's
    stale binding keep a tunnel up for good; the containers alone do not say which VNI carries
    them."""

    @staticmethod
    async def _spared(net: Any, registry: VniRegistry, live: dict[str, str]) -> frozenset[int]:
        net._vni_registry = registry

        async def containers() -> dict[str, str]:
            return live

        net._live_containers = containers
        spared: frozenset[int] = await net._other_agents_live_vnis()
        return spared

    async def test_another_agents_live_vni_is_spared(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path)
        async with registry.binding(5000, "i-other", "their-session", "d1") as bound:
            bound.mark_built()
        net = _network()
        spared = await self._spared(net, registry, {"c9": "their-session"})
        assert spared == frozenset({5000})

    async def test_our_own_vni_is_not_spared(self, tmp_path: Path) -> None:
        # The preflight exists for exactly these: our restart says nothing about their state.
        registry = VniRegistry(tmp_path)
        net = _network()
        async with registry.binding(5000, net._agent_id, "our-session", "d1") as bound:
            bound.mark_built()
        spared = await self._spared(net, registry, {"c1": "our-session"})
        assert spared == frozenset()

    async def test_a_binding_with_nothing_running_is_not_spared(self, tmp_path: Path) -> None:
        # A dead agent's leftover binding would otherwise keep a tunnel up for good.
        registry = VniRegistry(tmp_path)
        async with registry.binding(5000, "i-other", "gone", "d1") as bound:
            bound.mark_built()
        net = _network()
        spared = await self._spared(net, registry, {"c1": "some-other-session"})
        assert spared == frozenset()

    async def test_an_unreadable_registry_spares_nothing(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "does" / "not" / "exist")
        net = _network()
        spared = await self._spared(net, registry, {"c1": "whatever"})
        assert spared == frozenset()
