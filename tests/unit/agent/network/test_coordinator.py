import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any, cast, override
from unittest import mock

import ai.backend.agent.network.coordinator as coordinator_mod
from ai.backend.agent.network.coordinator import SessionNetworkCoordinator
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.network.keys import endpoints_prefix, member_key, members_prefix
from ai.backend.common.network.types import Member, NetworkBackendKind, SessionNetMeta

_META = SessionNetMeta(
    session_id="s1",
    subnet="10.128.5.0/24",
    backend=NetworkBackendKind.VXLAN,
    mtu=1450,
    vni=4097,
)
_SELF = Member(agent_id="a1", host_ip="10.0.0.1", vtep_ip="10.0.0.1")
_PEER2 = Member(agent_id="a2", host_ip="10.0.0.2", vtep_ip="10.0.0.2")
_PEER3 = Member(agent_id="a3", host_ip="10.0.0.3", vtep_ip="10.0.0.3")


class FakeEtcd:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def put(self, key: str, val: str, **kwargs: Any) -> None:
        self.store[key] = val

    async def delete(self, key: str, **kwargs: Any) -> None:
        self.store.pop(key, None)

    async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
        out: dict[str, str] = {}
        for key, val in self.store.items():
            if key.startswith(prefix):
                remainder = key[len(prefix) :]
                if "/" not in remainder:
                    out[remainder] = val
        return out

    async def watch_prefix(self, prefix: str, **kwargs: Any) -> AsyncIterator[None]:
        # No live events in unit tests; end the watch immediately.
        return
        yield  # pragma: no cover  (makes this an async generator)

    def seed_member(self, member: Member, session_id: str = "s1") -> None:
        self.store[member_key(session_id, member.agent_id)] = json.dumps({
            "host_ip": member.host_ip,
            "vtep_ip": member.vtep_ip,
        })

    def seed_endpoint(
        self,
        container_id: str,
        ip: str,
        mac: str,
        agent_id: str,
        session_id: str = "s1",
    ) -> None:
        self.store[f"{endpoints_prefix(session_id)}{container_id}"] = json.dumps({
            "ip": ip,
            "mac": mac,
            "agent_id": agent_id,
            "container_id": container_id,
        })


class _BlockingWatchEtcd(FakeEtcd):
    """A FakeEtcd whose watch never yields and never returns, so the coordinator's watch task
    stays live until it is cancelled — lets us assert stop() actually awaits the cancellation."""

    @override
    async def watch_prefix(self, prefix: str, **kwargs: Any) -> AsyncIterator[None]:
        await asyncio.Event().wait()  # blocks forever (until cancelled)
        yield  # pragma: no cover  (makes this an async generator)


class _ScriptedWatchEtcd(FakeEtcd):
    """Drives ``_watch`` through a fixed script of per-subscription outcomes so the retry/backoff
    loop can be exercised deterministically. Each entry is one ``watch_prefix`` call:

    - ``"end"``   — the stream ends immediately (an exhausted/closed watch),
    - ``"raise"`` — the subscription errors,
    - ``int n``   — yield ``n`` events, then end.
    """

    def __init__(self, behaviors: list[object]) -> None:
        super().__init__()
        self._behaviors = behaviors
        self.watch_calls = 0

    @override
    async def watch_prefix(self, prefix: str, **kwargs: Any) -> AsyncIterator[None]:
        i = self.watch_calls
        self.watch_calls += 1
        behavior = self._behaviors[i] if i < len(self._behaviors) else "end"
        if behavior == "raise":
            raise RuntimeError("etcd hiccup")
        if isinstance(behavior, int):
            for _ in range(behavior):
                yield None
            return
        # "end": exhausted stream — the yield above still makes this an async generator.
        return


class RecordingBackend:
    def __init__(self) -> None:
        self.setup: list[str] = []
        self.teardown: list[str] = []
        self.added: list[str] = []
        self.removed: list[str] = []
        self.endpoints_added: list[tuple[str, str]] = []
        self.endpoints_removed: list[tuple[str, str]] = []

    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        self.setup.append(meta.session_id)

    async def teardown_session_network(self, session_id: str) -> None:
        self.teardown.append(session_id)

    async def add_peer(self, session_id: str, peer: Member) -> None:
        self.added.append(peer.agent_id)

    async def del_peer(self, session_id: str, peer: Member) -> None:
        self.removed.append(peer.agent_id)

    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        self.endpoints_added.append((ip, vtep_ip))

    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        self.endpoints_removed.append((ip, vtep_ip))


class _FailingBackend(RecordingBackend):
    """RecordingBackend that can be told to fail specific device ops, to exercise the per-op
    failure isolation in reconcile_peers. ``add_peer`` raises for any agent_id in ``fail_add``;
    ``del_peer`` raises the first ``fail_del_times`` times it is called. Both still record the
    attempt so tests can assert it was tried."""

    def __init__(self, *, fail_add: set[str] | None = None, fail_del_times: int = 0) -> None:
        super().__init__()
        self.fail_add: set[str] = fail_add or set()
        self._fail_del_times = fail_del_times

    @override
    async def add_peer(self, session_id: str, peer: Member) -> None:
        if peer.agent_id in self.fail_add:
            raise RuntimeError(f"unroutable peer {peer.agent_id}")
        await super().add_peer(session_id, peer)

    @override
    async def del_peer(self, session_id: str, peer: Member) -> None:
        await super().del_peer(session_id, peer)  # record the attempt
        if self._fail_del_times > 0:
            self._fail_del_times -= 1
            raise RuntimeError(f"withdrawal failed for {peer.agent_id}")


def _coordinator(etcd: FakeEtcd, backend: RecordingBackend) -> SessionNetworkCoordinator:
    return SessionNetworkCoordinator(
        cast(AbstractKVStore, etcd),
        cast(Any, backend),
        agent_id="a1",
    )


class TestReconcilePeers:
    async def test_adds_new_peers_excluding_self(self) -> None:
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        etcd.seed_member(_PEER2)
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.reconcile_peers("s1")
        assert backend.added == ["a2"]  # self excluded

    async def test_is_idempotent(self) -> None:
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        etcd.seed_member(_PEER2)
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.reconcile_peers("s1")
        await coord.reconcile_peers("s1")
        assert backend.added == ["a2"]  # not re-added

    async def test_detects_new_and_removed_peers(self) -> None:
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        etcd.seed_member(_PEER2)
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.reconcile_peers("s1")

        etcd.seed_member(_PEER3)  # a3 joins
        await etcd.delete(member_key("s1", "a2"))  # a2 leaves
        await coord.reconcile_peers("s1")

        assert backend.added == ["a2", "a3"]
        assert backend.removed == ["a2"]

    async def test_a_failing_add_peer_is_isolated_and_retried(self) -> None:
        # One unroutable member used to abort the whole pass, leaving this node with no FDB/ARP for
        # anybody. A failing add_peer must be isolated: the other peers still apply, and the failed
        # one is left unapplied so the next reconcile retries exactly it.
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        etcd.seed_member(_PEER2)
        etcd.seed_member(_PEER3)
        backend = _FailingBackend(fail_add={"a2"})
        coord = _coordinator(etcd, backend)

        await coord.reconcile_peers("s1")
        # a2 raised, but a3 was still applied (not aborted by a2's failure).
        assert "a3" in backend.added

        backend.fail_add.clear()  # a2 becomes routable
        await coord.reconcile_peers("s1")
        # a2 was left unapplied, so this second pass retries and lands it; a3 is not re-added.
        assert backend.added == ["a3", "a2"]

    async def test_a_failing_del_peer_keeps_the_record_for_retry(self) -> None:
        # A departed peer whose withdrawal fails must NOT be forgotten — a dropped record would
        # leave a stale FDB entry unicasting to a dead VTEP forever. Keep it and retry.
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        etcd.seed_member(_PEER2)
        backend = _FailingBackend(fail_del_times=1)
        coord = _coordinator(etcd, backend)
        await coord.reconcile_peers("s1")

        await etcd.delete(member_key("s1", "a2"))  # a2 leaves
        await coord.reconcile_peers("s1")  # withdrawal fails once
        assert backend.removed == ["a2"]  # attempted
        await coord.reconcile_peers("s1")  # record kept -> retried and now succeeds
        assert backend.removed == ["a2", "a2"]


class TestStartStop:
    async def test_start_sets_up_writes_member_and_applies_peers(self) -> None:
        etcd = FakeEtcd()
        etcd.seed_member(_PEER2)  # a peer already present
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.start(_META, _SELF)
        try:
            assert backend.setup == ["s1"]
            assert member_key("s1", "a1") in etcd.store  # self published
            assert backend.added == ["a2"]  # existing peer applied
        finally:
            await coord.stop("s1")

    async def test_stop_tears_down_and_removes_membership(self) -> None:
        etcd = FakeEtcd()
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.start(_META, _SELF)
        assert member_key("s1", "a1") in etcd.store
        await coord.stop("s1")
        assert backend.teardown == ["s1"]
        assert member_key("s1", "a1") not in etcd.store

    async def test_stop_awaits_the_cancelled_watch_task(self) -> None:
        # With a live (blocked) watch, stop() must cancel AND await it, so no trailing reconcile
        # runs after teardown and the CancelledError is retrieved.
        etcd = _BlockingWatchEtcd()
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.start(_META, _SELF)
        task = coord._watch_tasks["s1"]
        assert not task.done()  # watch is live, blocked on events
        await coord.stop("s1")
        assert task.done()  # cancelled and awaited to completion


class TestReconcileEndpoints:
    async def test_programs_remote_endpoints_resolving_vtep(self) -> None:
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        etcd.seed_member(_PEER2)
        etcd.seed_endpoint("c-remote", "10.128.5.20", "02:42:0a:80:05:14", agent_id="a2")
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.reconcile_endpoints("s1")
        # remote endpoint programmed with its owner's VTEP (a2 -> 10.0.0.2)
        assert backend.endpoints_added == [("10.128.5.20", "10.0.0.2")]

    async def test_skips_own_endpoints(self) -> None:
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        etcd.seed_endpoint("c-local", "10.128.5.10", "02:42:0a:80:05:0a", agent_id="a1")
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.reconcile_endpoints("s1")
        assert backend.endpoints_added == []  # local endpoint not programmed

    async def test_skips_remote_without_published_vtep(self) -> None:
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        # a2's endpoint exists but a2's member (VTEP) not yet published
        etcd.seed_endpoint("c-remote", "10.128.5.20", "02:42:0a:80:05:14", agent_id="a2")
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.reconcile_endpoints("s1")
        assert backend.endpoints_added == []  # retried on a later watch tick

    async def test_idempotent_and_detects_removal(self) -> None:
        etcd = FakeEtcd()
        etcd.seed_member(_SELF)
        etcd.seed_member(_PEER2)
        etcd.seed_endpoint("c-remote", "10.128.5.20", "02:42:0a:80:05:14", agent_id="a2")
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        await coord.reconcile_endpoints("s1")
        await coord.reconcile_endpoints("s1")
        assert backend.endpoints_added == [("10.128.5.20", "10.0.0.2")]  # not re-added

        await etcd.delete(f"{endpoints_prefix('s1')}c-remote")
        await coord.reconcile_endpoints("s1")
        assert backend.endpoints_removed == [("10.128.5.20", "10.0.0.2")]


class _CancelAfter:
    """A drop-in for ``asyncio.sleep`` that records each backoff delay and then, once it has been
    called ``limit`` times, raises ``CancelledError`` to break ``_watch``'s infinite loop — the
    same way ``stop()`` would in production."""

    def __init__(self, limit: int) -> None:
        self.delays: list[float] = []
        self._limit = limit

    async def __call__(self, delay: float, *args: Any, **kwargs: Any) -> None:
        self.delays.append(delay)
        if len(self.delays) >= self._limit:
            raise asyncio.CancelledError()


class TestWatchRetryBackoff:
    """The watch loop must survive a failing/exhausted subscription and re-establish it, never
    ending for good and never hot-spinning — the multi-node worker-joins-late regression."""

    async def test_exhausted_stream_re_subscribes_after_a_backoff(self) -> None:
        # A watch that hands back an already-exhausted stream must NOT be re-subscribed in a tight
        # loop: each re-subscribe waits a backoff first (this is what stops the 100%-CPU spin).
        etcd = _ScriptedWatchEtcd(["end", "end", "end"])
        etcd.seed_member(_PEER2)  # visible only via the catch-up read, not a live event
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        sleep = _CancelAfter(limit=3)
        with mock.patch("asyncio.sleep", sleep):
            try:
                await coord._watch("s1")
            except asyncio.CancelledError:
                pass
        # slept before every re-subscribe (no hot-spin) and re-subscribed each time.
        assert len(sleep.delays) == 3
        assert etcd.watch_calls >= 3
        # the catch-up reconcile on re-subscribe applied the peer that the dead stream never
        # delivered as an event.
        assert "a2" in backend.added

    async def test_a_failing_subscription_is_retried_not_fatal(self) -> None:
        # A single etcd/device error used to end the loop for good, silently dropping the node from
        # the mesh for the rest of the session. It must be caught and retried instead.
        etcd = _ScriptedWatchEtcd(["raise", "raise", "raise"])
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        sleep = _CancelAfter(limit=3)
        with mock.patch("asyncio.sleep", sleep):
            try:
                await coord._watch("s1")
            except asyncio.CancelledError:
                pass
        assert etcd.watch_calls >= 3  # kept retrying past the first failure

    async def test_backoff_doubles_and_resets_when_events_flow(self) -> None:
        # Backoff grows exponentially across consecutive failures and snaps back to the base the
        # moment a live event arrives (the watch is healthy again).
        etcd = _ScriptedWatchEtcd(["end", "end", 1, "end"])  # 3rd subscription delivers one event
        backend = RecordingBackend()
        coord = _coordinator(etcd, backend)
        sleep = _CancelAfter(limit=3)
        with mock.patch("asyncio.sleep", sleep):
            try:
                await coord._watch("s1")
            except asyncio.CancelledError:
                pass
        base = coordinator_mod._WATCH_RETRY_BACKOFF
        # end -> base, end -> 2*base, then an event resets it -> base again.
        assert sleep.delays == [base, 2 * base, base]


class TestKeys:
    def test_members_prefix_and_member_key(self) -> None:
        assert members_prefix("s1") == "network/session/s1/members/"
        assert member_key("s1", "a2") == "network/session/s1/members/a2"
        assert endpoints_prefix("s1") == "network/session/s1/endpoints/"
