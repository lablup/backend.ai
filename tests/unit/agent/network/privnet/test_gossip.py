"""Wire and convergence rules for endpoint propagation between privnets.

The property every case here serves: a node's peers end up programming exactly the addresses that
node holds, from datagrams that may be lost, reordered, replayed, or forged.
"""

from __future__ import annotations

import json

import pytest

from ai.backend.agent.network.privnet.gossip import (
    MAX_AGE_SEC,
    PROTOCOL_VERSION,
    Announcement,
    Endpoint,
    PeerEndpoints,
    _sign,
    announcements_for,
    decode,
    peers_to_notify,
)

_KEY = "fda91fcdff70a287ce06dd57c2723324701c7ece94c53747ad8d4410483d639b"
_OTHER_KEY = "0" * 64
_VTEP = "192.168.0.156"
_PEER = "192.168.0.112"


def _endpoint(n: int) -> Endpoint:
    return Endpoint(
        container_id=f"{n:064x}",
        ip=f"10.128.2.{n}",
        mac=f"02:42:0a:80:02:{n:02x}",
        cluster_hostname=f"sub{n}",
    )


class TestTheWire:
    def test_an_announcement_survives_the_round_trip(self) -> None:
        sent = Announcement("s1", _VTEP, (_endpoint(1), _endpoint(2)), sent_at=1000.0)
        got = decode(sent.encode(_KEY), _KEY, now=1000.0)
        assert got == sent

    def test_a_datagram_signed_with_another_key_is_dropped(self) -> None:
        """The privnet holds CAP_NET_ADMIN and this is its first input from the network. A peer
        that cannot prove it shares the session's key is not a peer."""
        sent = Announcement("s1", _VTEP, (_endpoint(1),), sent_at=1000.0)
        assert decode(sent.encode(_OTHER_KEY), _KEY, now=1000.0) is None

    def test_a_tampered_body_is_dropped(self) -> None:
        raw = Announcement("s1", _VTEP, (_endpoint(1),), sent_at=1000.0).encode(_KEY)
        signature, _, body = raw.partition(b".")
        edited = json.loads(body)
        edited["e"][0]["i"] = "10.128.2.99"  # point a peer's MAC at another address
        assert decode(signature + b"." + json.dumps(edited).encode(), _KEY, now=1000.0) is None

    def test_a_stale_datagram_is_dropped(self) -> None:
        """Bounds replay: one captured off the underlay cannot be re-injected later to restore an
        endpoint that has since moved."""
        sent = Announcement("s1", _VTEP, (_endpoint(1),), sent_at=1000.0)
        assert decode(sent.encode(_KEY), _KEY, now=1000.0 + MAX_AGE_SEC + 1) is None

    def test_a_datagram_from_a_clock_slightly_ahead_is_kept(self) -> None:
        """Dropping these would show up as a peer that intermittently disappears."""
        sent = Announcement("s1", _VTEP, (_endpoint(1),), sent_at=1000.0)
        assert decode(sent.encode(_KEY), _KEY, now=990.0) is not None

    def test_an_unknown_version_is_refused_rather_than_guessed(self) -> None:
        body = json.dumps({"v": PROTOCOL_VERSION + 1, "s": "s1", "t": _VTEP, "e": [], "at": 1000.0})
        raw = _sign(body.encode(), _KEY) + b"." + body.encode()
        assert decode(raw, _KEY, now=1000.0) is None

    def test_one_malformed_entry_does_not_discard_the_rest(self) -> None:
        """The sender's other endpoints are still true; dropping them would black-hole live
        kernels over a field this node does not understand."""
        good = _endpoint(1)
        body = json.dumps({
            "v": PROTOCOL_VERSION,
            "s": "s1",
            "t": _VTEP,
            "e": [good.to_wire(), {"c": "x"}, "not-an-object"],
            "at": 1000.0,
            "p": 0,
            "n": 1,
        })
        got = decode(_sign(body.encode(), _KEY) + b"." + body.encode(), _KEY, now=1000.0)
        assert got is not None and got.endpoints == (good,)

    @pytest.mark.parametrize("bad", [b"", b"nodot", b".", b"abc.notjson"])
    def test_garbage_is_dropped_without_raising(self, bad: bytes) -> None:
        assert decode(bad, _KEY, now=1000.0) is None


class TestSlicing:
    """Whole state is what makes a lost datagram cost one interval instead of a missing entry, and
    a node with more endpoints than fit one datagram cannot put its whole state in one. So the
    unit of "whole" is the slice."""

    def test_a_node_that_fits_sends_one_datagram(self) -> None:
        out = announcements_for("s1", _VTEP, [_endpoint(1)], sent_at=1000.0, key=_KEY)
        assert len(out) == 1
        got = decode(out[0], _KEY, now=1000.0)
        assert got is not None and (got.part, got.parts) == (0, 1)

    def test_holding_nothing_still_announces(self) -> None:
        """ "I hold none" is the message that withdraws this node's last kernel from every peer."""
        out = announcements_for("s1", _VTEP, [], sent_at=1000.0, key=_KEY)
        assert len(out) == 1
        got = decode(out[0], _KEY, now=1000.0)
        assert got is not None and got.endpoints == ()

    def test_a_node_too_big_for_one_datagram_slices(self) -> None:
        many = [_endpoint(n) for n in range(1, 30)]
        out = announcements_for("s1", _VTEP, many, sent_at=1000.0, key=_KEY, max_bytes=400)
        assert len(out) > 1
        assert all(len(d) <= 400 or len(json.loads(d.partition(b".")[2])["e"]) == 1 for d in out)
        decoded = [decode(d, _KEY, now=1000.0) for d in out]
        assert all(d is not None for d in decoded)
        assert {a.part for a in decoded if a} == set(range(len(out)))
        assert {a.parts for a in decoded if a} == {len(out)}
        carried = [e for a in decoded if a for e in a.endpoints]
        assert sorted(carried, key=lambda e: e.container_id) == sorted(
            many, key=lambda e: e.container_id
        )


class TestConvergence:
    def test_a_peers_endpoints_are_applied(self) -> None:
        held = PeerEndpoints()
        added, removed = held.apply(
            Announcement("s1", _PEER, (_endpoint(1), _endpoint(2)), 1000.0), now=1000.0
        )
        assert added == {_endpoint(1), _endpoint(2)}
        assert removed == set()
        assert set(held.held("s1")) == {_endpoint(1).container_id, _endpoint(2).container_id}

    def test_a_repeat_announcement_programs_nothing(self) -> None:
        held = PeerEndpoints()
        announcement = Announcement("s1", _PEER, (_endpoint(1),), 1000.0)
        held.apply(announcement, now=1000.0)
        assert held.apply(announcement, now=1001.0) == (set(), set())

    def test_an_endpoint_that_stops_being_announced_is_withdrawn(self) -> None:
        """Nothing has to deliver a removal: absence from whole state IS the removal."""
        held = PeerEndpoints()
        held.apply(Announcement("s1", _PEER, (_endpoint(1), _endpoint(2)), 1000.0), now=1000.0)
        added, removed = held.apply(Announcement("s1", _PEER, (_endpoint(1),), 1001.0), now=1001.0)
        assert added == set()
        assert removed == {_endpoint(2)}

    def test_slices_do_not_overwrite_each_other(self) -> None:
        """The bug the slice index exists to prevent: replacing per sender would leave only the
        last datagram, so every endpoint but the final few would silently vanish."""
        held = PeerEndpoints()
        many = [_endpoint(n) for n in range(1, 12)]
        for datagram in announcements_for(
            "s1", _PEER, many, sent_at=1000.0, key=_KEY, max_bytes=400
        ):
            announcement = decode(datagram, _KEY, now=1000.0)
            assert announcement is not None
            held.apply(announcement, now=1000.0)
        assert set(held.held("s1")) == {e.container_id for e in many}

    def test_a_sender_that_shrinks_its_slice_count_drops_the_rest(self) -> None:
        """Three slices down to one: the other two are whole state for indices it no longer sends,
        so nothing would ever replace them and they would stay programmed for good."""
        held = PeerEndpoints()
        many = [_endpoint(n) for n in range(1, 12)]
        for datagram in announcements_for(
            "s1", _PEER, many, sent_at=1000.0, key=_KEY, max_bytes=400
        ):
            announcement = decode(datagram, _KEY, now=1000.0)
            assert announcement is not None
            held.apply(announcement, now=1000.0)

        survivor = _endpoint(1)
        (only,) = announcements_for("s1", _PEER, [survivor], sent_at=1001.0, key=_KEY)
        announcement = decode(only, _KEY, now=1001.0)
        assert announcement is not None
        _added, removed = held.apply(announcement, now=1001.0)

        assert set(held.held("s1")) == {survivor.container_id}
        assert survivor not in removed

    def test_two_peers_are_held_apart(self) -> None:
        """An endpoint moves when its kernel is re-created on another node, and both nodes then
        name the same container. Replacing per sender is what makes the move converge."""
        held = PeerEndpoints()
        moved = _endpoint(1)
        held.apply(Announcement("s1", _PEER, (moved,), 1000.0), now=1000.0)
        held.apply(Announcement("s1", "192.168.0.104", (moved,), 1001.0), now=1001.0)
        held.apply(Announcement("s1", _PEER, (), 1002.0), now=1002.0)

        assert held.held("s1") == {moved.container_id: (moved, "192.168.0.104")}

    def test_a_session_is_forgotten_whole(self) -> None:
        held = PeerEndpoints()
        held.apply(Announcement("s1", _PEER, (_endpoint(1),), 1000.0), now=1000.0)
        held.apply(Announcement("s2", _PEER, (_endpoint(2),), 1000.0), now=1000.0)
        held.forget_session("s1")
        assert held.held("s1") == {}
        assert set(held.held("s2")) == {_endpoint(2).container_id}

    def test_forgetting_a_peer_returns_what_it_had(self) -> None:
        """A node leaving is the manager's statement. What it was holding has to come back so the
        caller can unprogram exactly that."""
        held = PeerEndpoints()
        held.apply(Announcement("s1", _PEER, (_endpoint(1), _endpoint(2)), 1000.0), now=1000.0)
        assert held.forget_peer("s1", _PEER) == {_endpoint(1), _endpoint(2)}
        assert held.held("s1") == {}

    def test_silence_is_reported_but_is_not_a_withdrawal(self) -> None:
        """Withdrawing a quiet peer's kernels would cut a live session over a pause."""
        held = PeerEndpoints()
        held.apply(Announcement("s1", _PEER, (_endpoint(1),), 1000.0), now=1000.0)
        assert held.silent_peers("s1", now=1100.0, older_than=30.0) == {_PEER}
        assert set(held.held("s1")) == {_endpoint(1).container_id}


class TestWhoIsTold:
    def test_a_node_does_not_announce_to_itself(self) -> None:
        """It would program its own kernels' MACs against its own VTEP -- a tunnel to nowhere,
        while those containers are already on the bridge directly."""
        assert peers_to_notify([_VTEP, _PEER], _VTEP) == [_PEER]

    def test_no_peers_is_no_datagrams(self) -> None:
        assert peers_to_notify(None, _VTEP) == []
        assert peers_to_notify([_VTEP], _VTEP) == []

    def test_duplicates_are_collapsed(self) -> None:
        assert peers_to_notify([_PEER, _PEER, ""], _VTEP) == [_PEER]
