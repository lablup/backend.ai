import json
from collections.abc import AsyncIterator
from typing import Any, cast

from ai.backend.agent.network.coordinator import (
    SessionNetworkCoordinator,
    member_key,
    members_prefix,
)
from ai.backend.common.etcd import AbstractKVStore
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
                remainder = key[len(prefix):]
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
            "ip_range": member.ip_range,
        })


class RecordingBackend:
    def __init__(self) -> None:
        self.setup: list[str] = []
        self.teardown: list[str] = []
        self.added: list[str] = []
        self.removed: list[str] = []

    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        self.setup.append(meta.session_id)

    async def teardown_session_network(self, session_id: str) -> None:
        self.teardown.append(session_id)

    async def add_peer(self, session_id: str, peer: Member) -> None:
        self.added.append(peer.agent_id)

    async def del_peer(self, session_id: str, peer: Member) -> None:
        self.removed.append(peer.agent_id)


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


class TestKeys:
    def test_members_prefix_and_member_key(self) -> None:
        assert members_prefix("s1") == "network/session/s1/members/"
        assert member_key("s1", "a2") == "network/session/s1/members/a2"
