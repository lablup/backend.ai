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

import json
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
        self,
        *,
        preflight_error: Exception | None = None,
        still_up: frozenset[str] = frozenset(),
        debt: dict[str, str] | None = None,
        clears_debt_after: int = 1 << 30,
    ) -> None:
        self.preflight_error = preflight_error
        self.still_up = still_up
        self.preflight_calls = 0
        self.spared: frozenset[int] = frozenset()
        self.retry_calls = 0
        #: What a failed setup left on the host that this backend could not take back.
        self.debt = dict(debt or {})
        self.clears_debt_after = clears_debt_after

    async def prepare_recovery(self, spare: Collection[int] = ()) -> None:
        self.preflight_calls += 1
        self.spared = frozenset(spare)
        if self.preflight_error is not None:
            raise self.preflight_error

    async def retry_fail_close(self) -> frozenset[str]:
        self.retry_calls += 1
        self.debt = dict(self.debt) if self.retry_calls < self.clears_debt_after else {}
        return self.still_up | frozenset(self.debt)

    def cleanup_debt(self) -> dict[str, str]:
        return dict(self.debt)


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
    async def _spared(
        net: Any, registry: VniRegistry, live: set[tuple[str, str]]
    ) -> frozenset[int]:
        net._vni_registry = registry

        async def running() -> set[tuple[str, str]]:
            return live

        net._live_session_owners = running
        spared: frozenset[int] = await net._other_agents_live_vnis()
        return spared

    async def test_another_agents_live_vni_is_spared(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path)
        async with registry.binding(5000, "i-other", "their-session", "d1") as bound:
            bound.mark_built()
        net = _network()
        spared = await self._spared(net, registry, {("their-session", "i-other")})
        assert spared == frozenset({5000})

    async def test_our_own_vni_is_not_spared(self, tmp_path: Path) -> None:
        # The preflight exists for exactly these: our restart says nothing about their state.
        registry = VniRegistry(tmp_path)
        net = _network()
        async with registry.binding(5000, net._agent_id, "our-session", "d1") as bound:
            bound.mark_built()
        spared = await self._spared(net, registry, {("our-session", net._agent_id)})
        assert spared == frozenset()

    async def test_a_binding_with_nothing_running_is_not_spared(self, tmp_path: Path) -> None:
        # A dead agent's leftover binding would otherwise keep a tunnel up for good.
        registry = VniRegistry(tmp_path)
        async with registry.binding(5000, "i-other", "gone", "d1") as bound:
            bound.mark_built()
        net = _network()
        spared = await self._spared(net, registry, {("some-other-session", "i-other")})
        assert spared == frozenset()

    async def test_a_binding_that_only_reserved_the_vni_is_not_spared(self, tmp_path: Path) -> None:
        # HELD, never built: it describes no device, so there is nothing to spare and the
        # fail-close is what should decide.
        registry = VniRegistry(tmp_path)
        async with registry.binding(5000, "i-other", "their-session", "d1"):
            pass
        net = _network()
        spared = await self._spared(net, registry, {("their-session", "i-other")})
        assert spared == frozenset()

    async def test_a_container_of_another_agent_does_not_vouch_for_a_third(
        self, tmp_path: Path
    ) -> None:
        # The binding is i-other's and the running container is i-third's. Neither says i-other's
        # tunnel is live, and excepting it from the fail-close on that basis is the bypass.
        registry = VniRegistry(tmp_path)
        async with registry.binding(5000, "i-other", "their-session", "d1") as bound:
            bound.mark_built()
        net = _network()
        spared = await self._spared(net, registry, {("their-session", "i-third")})
        assert spared == frozenset()

    async def test_an_unreadable_registry_spares_nothing(self, tmp_path: Path) -> None:
        registry = VniRegistry(tmp_path / "does" / "not" / "exist")
        net = _network()
        spared = await self._spared(net, registry, {("whatever", "i-other")})
        assert spared == frozenset()


class _Etcd:
    """The one call `_read_session_meta` makes."""

    def __init__(self, store: dict[str, str]) -> None:
        self.store = store

    async def get(self, key: str) -> str | None:
        return self.store.get(key)


class TestARecordTheManagerHasNotFinished:
    """The manager's session record carries how far it got. Anything but "ready" names a subnet
    and a VNI committed to nobody -- a create still running, or one undoing itself -- and it
    carries none of the rest of the meta. Reading it as a session is how a node builds a data
    plane on an allocation the pool is about to hand to somebody else."""

    _READY = {"subnet": "10.128.5.0/24", "vni": 4097, "backend": "vxlan", "mtu": 1450}

    def _network_reading(self, record: dict[str, Any] | None) -> SessionNetwork:
        store = {} if record is None else {"network/session/s1/meta": json.dumps(record)}
        network = _network(vxlan=_Backend())
        network._etcd = cast(Any, _Etcd(store))
        return network

    async def test_a_tombstone_is_not_a_session(self) -> None:
        network = self._network_reading({**self._READY, "_state": "deleting"})
        assert await network._read_session_meta("s1") is None

    async def test_neither_is_one_still_being_built(self) -> None:
        network = self._network_reading({"_owner": "tok1", "_state": "creating"})
        assert await network._read_session_meta("s1") is None

    async def test_a_finished_one_is(self) -> None:
        network = self._network_reading({**self._READY, "_state": "ready"})
        meta = await network._read_session_meta("s1")
        assert meta is not None and meta.vni == 4097

    async def test_and_so_is_our_own_single_node_meta_which_has_no_state(self) -> None:
        network = self._network_reading(self._READY)
        meta = await network._read_session_meta("s1")
        assert meta is not None and meta.subnet == "10.128.5.0/24"


class TestWhatAFailedSetupStillOwes:
    """A setup that failed leaves rules behind long after recovery is over. Nothing else comes
    back for them, and the value this returns IS what the agent publishes as its readiness -- so
    a node whose backend refuses every new session must not be reported as ready."""

    _DEBT = {"vxlan:leftover:vni4097": "rules that would drop the next session on this VNI"}

    async def test_a_backend_that_owes_is_retried_even_though_recovery_succeeded(self) -> None:
        backend = _Backend(debt=dict(self._DEBT))
        network = _network(vxlan=backend)
        # Nothing failed recovery: the backend is not in `_recovery_incomplete`, and the retry
        # used to walk only over that.
        assert "vxlan" not in network._recovery_incomplete

        await network.retry_recovery_fail_close()

        assert backend.retry_calls == 1, "the debt was never retried"

    async def test_the_debt_goes_out_with_the_readiness_report(self) -> None:
        backend = _Backend(debt=dict(self._DEBT))
        network = _network(vxlan=backend)
        reported = await network.retry_recovery_fail_close()
        assert "vxlan:leftover:vni4097" in reported

    async def test_it_stops_being_reported_once_it_is_gone(self) -> None:
        backend = _Backend(debt=dict(self._DEBT), clears_debt_after=1)
        network = _network(vxlan=backend)
        reported = await network.retry_recovery_fail_close()
        assert "vxlan:leftover:vni4097" not in reported
        assert "vxlan:leftover:vni4097" not in network.recovery_problems()

    async def test_debt_alone_does_not_count_as_a_tunnel_left_up(self) -> None:
        # `_recovery_incomplete` is for what recovery could not close; conflating the two would
        # hold up the stale-claim prune over rules that no surviving tunnel has anything to do
        # with.
        backend = _Backend(debt=dict(self._DEBT))
        network = _network(vxlan=backend)
        await network.retry_recovery_fail_close()
        assert "vxlan" not in network._recovery_incomplete


class _PrefixEtcd(_Etcd):
    """`_Etcd` plus the prefix read the departed-session sweep makes."""

    def __init__(self, store: dict[str, str], tree: dict[str, Any] | None = None) -> None:
        super().__init__(store)
        self.tree = tree or {}
        self.prefixes_read: list[str] = []

    async def get_prefix(self, prefix: str) -> dict[str, Any]:
        self.prefixes_read.append(prefix)
        return self.tree


class TestSessionsThisNodeIsStillAMemberOf:
    """`recover` walks the sessions of *live containers*. A session whose last container here died
    while the agent was down has none, so nothing visited it and its member key stayed -- and the
    manager will not release the VNI while a member has not confirmed teardown. Measured: two
    sessions stuck in TERMINATING with both kernels already TERMINATED, the manager retrying
    `destroy_network` every fifteen seconds against a node that was never going to answer.
    """

    def _network_seeing(self, tree: dict[str, Any]) -> tuple[SessionNetwork, _PrefixEtcd]:
        network = _network(vxlan=_Backend())
        etcd = _PrefixEtcd({}, tree)
        network._etcd = cast(Any, etcd)
        return network, etcd

    async def test_a_session_naming_this_agent_is_found(self) -> None:
        network, _etcd = self._network_seeing({
            "s1": {"members": {"i-test": "{}"}},
            "s2": {"members": {"i-other": "{}"}},
        })
        assert await network._sessions_naming_this_node() == {"s1"}

    async def test_a_session_with_no_members_at_all_is_not(self) -> None:
        network, _etcd = self._network_seeing({"s1": {"meta": "{}"}})
        assert await network._sessions_naming_this_node() == set()

    async def test_the_whole_subtree_is_read_once(self) -> None:
        """One prefix read for the node, not one per session: the sweep runs on every restart."""
        network, etcd = self._network_seeing({"s1": {"members": {"i-test": "{}"}}})
        await network._sessions_naming_this_node()
        assert etcd.prefixes_read == ["network/session/"]

    async def test_a_malformed_subtree_is_skipped_not_raised(self) -> None:
        """etcd hands back whatever is there. A node that cannot finish this sweep would abort its
        own recovery, which is worse than missing one stale membership."""
        network, _etcd = self._network_seeing({
            "s1": "not-a-mapping",
            "s2": {"members": "also-not-a-mapping"},
            "s3": {"members": {"i-test": "{}"}},
        })
        assert await network._sessions_naming_this_node() == {"s3"}


class TestFinishingWhatTheRestartInterrupted:
    """What the sweep does with what it found. Resume-then-tear-down rather than deleting the
    member key: the withdrawal is fenced, and the same path gives back the bridge, the LOCAL block
    and the ESP claim, none of which removing a key would."""

    _READY = {
        "subnet": "10.128.5.0/24",
        "vni": 4097,
        "backend": "vxlan",
        "mtu": 1450,
        "_state": "ready",
    }

    def _network_with(
        self,
        monkeypatch: pytest.MonkeyPatch,
        joined: set[str],
        metas: dict[str, dict[str, Any]],
    ) -> tuple[SessionNetwork, list[str], list[str]]:
        network = _network(vxlan=_Backend())
        store = {f"network/session/{s}/meta": json.dumps(m) for s, m in metas.items()}
        tree = {s: {"members": {"i-test": "{}"}} for s in joined}
        network._etcd = cast(Any, _PrefixEtcd(store, tree))
        resumed: list[str] = []
        torn: list[str] = []

        async def _resume(session_id: str, meta: Any) -> None:
            resumed.append(session_id)

        async def _teardown(session_id: str) -> None:
            torn.append(session_id)

        monkeypatch.setattr(network, "_resume_session", _resume)
        monkeypatch.setattr(network, "teardown_session", _teardown)
        return network, resumed, torn

    async def test_a_departed_session_is_resumed_then_torn_down(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        network, resumed, torn = self._network_with(monkeypatch, {"s1"}, {"s1": self._READY})
        await network._finish_departed_sessions(set())
        assert resumed == ["s1"], "without resuming there is no coordinator to withdraw through"
        assert torn == ["s1"]

    async def test_a_session_this_node_still_runs_is_left_alone(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The argument is what `recover` already resumed from live containers. Tearing one of
        those down would take the data plane out from under running kernels."""
        network, resumed, torn = self._network_with(monkeypatch, {"s1"}, {"s1": self._READY})
        await network._finish_departed_sessions({"s1"})
        assert (resumed, torn) == ([], [])

    async def test_a_session_with_no_readable_meta_is_left_alone(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The manager deletes the meta as the last step of `destroy_network`, so an absent one
        means it is no longer waiting on anybody -- and there is no data plane to rebuild."""
        network, resumed, torn = self._network_with(monkeypatch, {"s1"}, {})
        await network._finish_departed_sessions(set())
        assert (resumed, torn) == ([], [])

    async def test_a_meta_the_manager_has_not_finished_is_left_alone(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        network, resumed, torn = self._network_with(
            monkeypatch, {"s1"}, {"s1": {**self._READY, "_state": "deleting"}}
        )
        await network._finish_departed_sessions(set())
        assert (resumed, torn) == ([], [])

    async def test_one_that_will_not_go_does_not_stop_the_others(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        network, resumed, torn = self._network_with(
            monkeypatch, {"s1", "s2"}, {"s1": self._READY, "s2": self._READY}
        )
        original = network.teardown_session

        async def _teardown(session_id: str) -> None:
            if session_id == "s1":
                raise RuntimeError("still holding a container")
            await original(session_id)

        monkeypatch.setattr(network, "teardown_session", _teardown)
        await network._finish_departed_sessions(set())
        assert torn == ["s2"], "s2's teardown must still have run"
        assert any("s1" in key for key in network.recovery_problems()), (
            "a session that could not be finished has to reach readiness, or the node keeps"
            " taking overlay work while the manager waits on it forever"
        )

    async def test_an_unreadable_etcd_does_not_abort_recovery(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        network, resumed, torn = self._network_with(monkeypatch, {"s1"}, {"s1": self._READY})

        async def _boom(prefix: str) -> dict[str, Any]:
            raise RuntimeError("etcd is down")

        monkeypatch.setattr(network._etcd, "get_prefix", _boom)
        await network._finish_departed_sessions(set())
        assert (resumed, torn) == ([], [])
        assert "departed-sessions" in network.recovery_problems()


class _EmptyLocator:
    """A node with no kernel containers left on it -- which is exactly the state that hid the
    stranded sessions: nothing live means nothing for `recover` to walk."""

    async def live_sessions(self) -> dict[str, Any]:
        return {}


class TestTheSweepIsWiredIntoRecovery:
    """The methods above are only worth having if `recover` calls them. It did not, for the whole
    life of the branch, and the sessions it should have finished sat in TERMINATING for good."""

    async def test_recover_finishes_the_sessions_it_did_not_walk(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        network = _network(vxlan=_Backend())
        network._locator = cast(Any, _EmptyLocator())
        network._etcd = cast(Any, _PrefixEtcd({}, {"s1": {"members": {"i-test": "{}"}}}))
        swept: list[frozenset[str]] = []

        async def _sweep(resumed: set[str]) -> None:
            swept.append(frozenset(resumed))

        monkeypatch.setattr(network, "_finish_departed_sessions", _sweep)
        await network.recover()
        assert swept == [frozenset()], (
            "recover did not sweep the sessions that still name this node, so a membership left"
            " by an interrupted teardown is never withdrawn"
        )

    async def test_the_sweep_is_told_what_recovery_already_resumed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """It must not tear down a session whose kernels are running here."""

        class _OneLiveKernel:
            async def live_sessions(self) -> dict[str, Any]:
                container = type("C", (), {"session_id": "s-live", "owner_agent_id": "i-test"})()
                return {"c1": container}

        network = _network(vxlan=_Backend())
        network._locator = cast(Any, _OneLiveKernel())
        network._etcd = cast(Any, _PrefixEtcd({}, {}))
        swept: list[frozenset[str]] = []

        async def _sweep(resumed: set[str]) -> None:
            swept.append(frozenset(resumed))

        monkeypatch.setattr(network, "_finish_departed_sessions", _sweep)
        await network.recover()
        assert swept == [frozenset({"s-live"})]
