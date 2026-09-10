"""What the endpoint exchange does when it is driven: over fakes, and over a real loopback socket.

The socket cases are here because the rules and the transport can each be right while the wiring
between them is not -- a datagram sent to the wrong port, an announcement built for a peer that is
this node itself, a receiver that never programs what it decoded.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from ai.backend.agent.network.privnet.gossip import Endpoint
from ai.backend.agent.network.privnet.gossip_runner import EndpointGossip

_KEY = "fda91fcdff70a287ce06dd57c2723324701c7ece94c53747ad8d4410483d639b"


class FakeHost:
    """A privnet, as far as the exchange can see one."""

    def __init__(
        self,
        *,
        sessions: dict[str, list[Endpoint]],
        peers: dict[str, list[str]],
        key: str | None = _KEY,
        generation: str | None = None,
    ) -> None:
        self._sessions = sessions
        self._peers = peers
        self._key = key
        self._generation = generation
        self.programmed: list[tuple[str, str, Endpoint, str]] = []

    def gossip_key(self) -> str | None:
        return self._key

    def gossip_sessions(self) -> Sequence[str]:
        return list(self._sessions)

    def gossip_peers(self, session_id: str) -> Sequence[str]:
        return self._peers.get(session_id, [])

    def gossip_local_endpoints(self, session_id: str) -> Sequence[Endpoint]:
        return self._sessions.get(session_id, [])

    def gossip_generation(self, session_id: str) -> str | None:
        return self._generation

    async def gossip_program(
        self,
        session_id: str,
        *,
        add: Sequence[tuple[Endpoint, str]],
        remove: Sequence[tuple[Endpoint, str]],
    ) -> None:
        for endpoint, vtep in add:
            self.programmed.append(("add", session_id, endpoint, vtep))
        for endpoint, vtep in remove:
            self.programmed.append(("remove", session_id, endpoint, vtep))

    def added(self) -> set[str]:
        return {e.container_id for op, _s, e, _v in self.programmed if op == "add"}

    def removed(self) -> set[str]:
        return {e.container_id for op, _s, e, _v in self.programmed if op == "remove"}


def _endpoint(n: int) -> Endpoint:
    return Endpoint(container_id=f"{n:064x}", ip=f"10.128.2.{n}", mac=f"02:42:0a:80:02:{n:02x}")


class TestWhatARunnerSends:
    async def test_it_does_not_announce_to_itself(self) -> None:
        """A node programming its own kernels against its own VTEP is a tunnel to nowhere, and
        those containers are already on the bridge directly."""
        host = FakeHost(sessions={"s1": [_endpoint(1)]}, peers={"s1": ["10.0.0.1"]})
        sent: list[tuple[bytes, tuple[str, int]]] = []
        gossip = EndpointGossip(host, vtep="10.0.0.1", port=7947)
        gossip._transport = _FakeTransport(sent)  # type: ignore[assignment]

        gossip.announce("s1")

        assert sent == []

    async def test_it_announces_whole_state_to_every_peer(self) -> None:
        host = FakeHost(
            sessions={"s1": [_endpoint(1), _endpoint(2)]},
            peers={"s1": ["10.0.0.1", "10.0.0.2", "10.0.0.3"]},
        )
        sent: list[tuple[bytes, tuple[str, int]]] = []
        gossip = EndpointGossip(host, vtep="10.0.0.1", port=7947)
        gossip._transport = _FakeTransport(sent)  # type: ignore[assignment]

        gossip.announce("s1")

        assert {addr for _d, addr in sent} == {("10.0.0.2", 7947), ("10.0.0.3", 7947)}

    async def test_a_node_with_no_key_yet_says_nothing(self) -> None:
        """Signing is not optional: an unsigned announcement is one any host that can reach the
        port could have written."""
        host = FakeHost(sessions={"s1": [_endpoint(1)]}, peers={"s1": ["10.0.0.2"]}, key=None)
        sent: list[tuple[bytes, tuple[str, int]]] = []
        gossip = EndpointGossip(host, vtep="10.0.0.1", port=7947)
        gossip._transport = _FakeTransport(sent)  # type: ignore[assignment]

        gossip.announce("s1")

        assert sent == []

    async def test_a_send_that_fails_is_not_a_session_failure(self) -> None:
        """Whole state means the next interval corrects it, so a peer that is briefly unreachable
        must not take the pass down with it."""
        host = FakeHost(sessions={"s1": [_endpoint(1)]}, peers={"s1": ["10.0.0.2", "10.0.0.3"]})
        sent: list[tuple[bytes, tuple[str, int]]] = []
        gossip = EndpointGossip(host, vtep="10.0.0.1", port=7947)
        gossip._transport = _FakeTransport(sent, fail_for="10.0.0.2")  # type: ignore[assignment]

        gossip.announce("s1")  # must not raise

        assert {addr for _d, addr in sent} == {("10.0.0.3", 7947)}


class TestWhatARunnerAppliesOnReceipt:
    async def test_an_unsigned_datagram_programs_nothing(self) -> None:
        host = FakeHost(sessions={"s1": []}, peers={})
        gossip = EndpointGossip(host, vtep="10.0.0.1")
        await gossip.on_datagram(b"whatever", ("10.0.0.2", 7947))
        assert host.programmed == []

    async def test_an_announcement_for_an_unknown_session_is_ignored(self) -> None:
        """Not an error: a peer may still be announcing a session this node already tore down."""
        sender = FakeHost(sessions={"s9": [_endpoint(1)]}, peers={"s9": ["10.0.0.1"]})
        receiver = FakeHost(sessions={"s1": []}, peers={})
        datagram = _one_datagram(sender, "s9", vtep="10.0.0.2")

        await EndpointGossip(receiver, vtep="10.0.0.1").on_datagram(datagram, ("10.0.0.2", 7947))

        assert receiver.programmed == []

    async def test_another_incarnation_is_ignored(self) -> None:
        """A session id is reused; an announcement from the previous incarnation names addresses
        the live one does not hold, and programming them points the FDB at a kernel that is gone."""
        sender = FakeHost(
            sessions={"s1": [_endpoint(1)]}, peers={"s1": ["10.0.0.1"]}, generation="old"
        )
        receiver = FakeHost(sessions={"s1": []}, peers={}, generation="new")
        datagram = _one_datagram(sender, "s1", vtep="10.0.0.2")

        await EndpointGossip(receiver, vtep="10.0.0.1").on_datagram(datagram, ("10.0.0.2", 7947))

        assert receiver.programmed == []

    async def test_a_repeat_announcement_programs_nothing_twice(self) -> None:
        sender = FakeHost(sessions={"s1": [_endpoint(1)]}, peers={"s1": ["10.0.0.1"]})
        receiver = FakeHost(sessions={"s1": []}, peers={})
        gossip = EndpointGossip(receiver, vtep="10.0.0.1")
        datagram = _one_datagram(sender, "s1", vtep="10.0.0.2")

        await gossip.on_datagram(datagram, ("10.0.0.2", 7947))
        await gossip.on_datagram(datagram, ("10.0.0.2", 7947))

        assert len(receiver.programmed) == 1


class TestMembershipIsTheAuthorityOnLeaving:
    async def test_a_departed_peer_is_unprogrammed(self) -> None:
        sender = FakeHost(sessions={"s1": [_endpoint(1)]}, peers={"s1": ["10.0.0.1"]})
        receiver = FakeHost(sessions={"s1": []}, peers={"s1": ["10.0.0.1", "10.0.0.2"]})
        gossip = EndpointGossip(receiver, vtep="10.0.0.1")
        gossip._transport = _FakeTransport([])  # type: ignore[assignment]
        gossip.announce("s1")  # learn the current membership
        await gossip.on_datagram(_one_datagram(sender, "s1", vtep="10.0.0.2"), ("10.0.0.2", 7947))
        assert receiver.added() == {_endpoint(1).container_id}

        receiver._peers["s1"] = ["10.0.0.1"]  # the manager dropped the peer
        await gossip.drop_departed_peers("s1")

        assert receiver.removed() == {_endpoint(1).container_id}

    async def test_silence_alone_never_withdraws(self) -> None:
        """A peer that has merely paused would have its live kernels cut."""
        sender = FakeHost(sessions={"s1": [_endpoint(1)]}, peers={"s1": ["10.0.0.1"]})
        receiver = FakeHost(sessions={"s1": []}, peers={"s1": ["10.0.0.1", "10.0.0.2"]})
        gossip = EndpointGossip(receiver, vtep="10.0.0.1")
        gossip._transport = _FakeTransport([])  # type: ignore[assignment]
        gossip.announce("s1")
        await gossip.on_datagram(_one_datagram(sender, "s1", vtep="10.0.0.2"), ("10.0.0.2", 7947))

        await gossip.drop_departed_peers("s1")  # membership unchanged, peer merely quiet

        assert receiver.removed() == set()


class TestTwoNodesOverALoopbackSocket:
    """The wiring the fakes cannot check: a real datagram, a real port, a real receiver."""

    async def test_a_kernel_on_one_node_reaches_the_other_nodes_table(self) -> None:
        port = 47947
        a_host = FakeHost(sessions={"s1": [_endpoint(1)]}, peers={"s1": ["127.0.0.1", "127.0.0.2"]})
        b_host = FakeHost(sessions={"s1": []}, peers={"s1": ["127.0.0.1", "127.0.0.2"]})
        a = EndpointGossip(a_host, vtep="127.0.0.1", port=port, interval=0.05)
        b = EndpointGossip(b_host, vtep="127.0.0.2", port=port, interval=0.05)
        await a.start()
        await b.start()
        try:
            a.announce("s1")
            async with asyncio.timeout(5):
                while not b_host.programmed:
                    await asyncio.sleep(0.02)
        finally:
            await a.stop()
            await b.stop()

        op, session_id, endpoint, vtep = b_host.programmed[0]
        assert (op, session_id, endpoint.container_id, vtep) == (
            "add",
            "s1",
            _endpoint(1).container_id,
            "127.0.0.1",
        )

    async def test_the_timer_re_announces_without_being_asked(self) -> None:
        """The whole retry story: a peer that was restarting catches up at the next interval with
        nothing having been retried or acknowledged."""
        port = 47948
        a_host = FakeHost(sessions={"s1": [_endpoint(1)]}, peers={"s1": ["127.0.0.1", "127.0.0.2"]})
        b_host = FakeHost(sessions={"s1": []}, peers={"s1": ["127.0.0.1", "127.0.0.2"]})
        a = EndpointGossip(a_host, vtep="127.0.0.1", port=port, interval=0.05)
        b = EndpointGossip(b_host, vtep="127.0.0.2", port=port, interval=0.05)
        await a.start()
        try:
            await asyncio.sleep(0.15)  # a announces into the void; b is not up yet
            await b.start()
            async with asyncio.timeout(5):
                while not b_host.programmed:
                    await asyncio.sleep(0.02)
        finally:
            await a.stop()
            await b.stop()

        assert b_host.added() == {_endpoint(1).container_id}


def _one_datagram(host: FakeHost, session_id: str, *, vtep: str) -> bytes:
    sent: list[tuple[bytes, tuple[str, int]]] = []
    gossip = EndpointGossip(host, vtep=vtep, port=7947)
    gossip._transport = _FakeTransport(sent)  # type: ignore[assignment]
    gossip.announce(session_id)
    assert sent, "the fixture expected this host to announce"
    return sent[0][0]


class _FakeTransport:
    def __init__(
        self, sent: list[tuple[bytes, tuple[str, int]]], *, fail_for: str | None = None
    ) -> None:
        self._sent = sent
        self._fail_for = fail_for

    def sendto(self, data: bytes, addr: tuple[str, int]) -> None:
        if self._fail_for is not None and addr[0] == self._fail_for:
            raise OSError("network unreachable")
        self._sent.append((data, addr))

    def close(self) -> None:
        pass
