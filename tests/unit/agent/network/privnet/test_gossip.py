"""Wire and convergence rules for endpoint propagation between privnets.

The property every case here serves: a node's peers end up programming exactly the addresses that
node holds, from datagrams that may be lost, reordered, replayed, or forged.
"""

from __future__ import annotations

import json
import random

import pytest

from ai.backend.agent.network.privnet.gossip import (
    MAX_AGE_SEC,
    PROTOCOL_VERSION,
    Announcement,
    Endpoint,
    GossipState,
    Intent,
    _sign,
    announcements_for,
    decode,
    endpoints_of,
    peers_to_notify,
)
from ai.backend.common.network.types import mac_for_ip

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


def _state(*peers: str, session: str = "s1", now: float = 900.0) -> GossipState:
    """A state machine whose membership already names `peers` -- the only thing that admits one."""
    state = GossipState()
    state.on_membership(session, peers or (_PEER,), now=now)
    return state


def _deliver(
    state: GossipState,
    announcement: Announcement,
    *,
    now: float | None = None,
) -> list[Intent]:
    """One datagram in, the convergence it produces out, all of it confirmed."""
    state.on_datagram(announcement, now=announcement.sent_at if now is None else now)
    intents = state.converge(announcement.session_id)
    state.confirm(announcement.session_id, applied=intents)
    return intents


class TestAdmission:
    """Membership creates a peer's state, and a datagram never does. A sender the session does not
    name has nothing here to drive, whatever key signed it -- which is the isolation a
    cluster-wide gossip key cannot provide on its own."""

    def test_a_sender_the_session_does_not_name_is_ignored(self) -> None:
        state = _state(_PEER)
        stranger = Announcement("s1", "192.168.0.9", (_endpoint(1),), 1000.0)
        assert _deliver(state, stranger) == []
        assert state.held("s1") == {}

    def test_a_peer_the_membership_adds_is_then_accepted(self) -> None:
        state = _state(_PEER)
        state.on_membership("s1", [_PEER, "192.168.0.9"], now=1000.0)
        joined = Announcement("s1", "192.168.0.9", (_endpoint(1),), 1000.0)
        assert [i.action for i in _deliver(state, joined)] == ["add"]

    def test_a_peer_the_membership_drops_is_unprogrammed(self) -> None:
        """A node leaving is the manager's statement, and it is the only thing that withdraws."""
        state = _state(_PEER)
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1000.0))
        state.on_membership("s1", [], now=1001.0)
        intents = state.converge("s1")
        assert [(i.action, i.endpoint) for i in intents] == [("remove", _endpoint(1))]


class TestConvergence:
    def test_a_peers_endpoints_are_applied(self) -> None:
        state = _state()
        intents = _deliver(state, Announcement("s1", _PEER, (_endpoint(1), _endpoint(2)), 1000.0))
        assert {(i.action, i.endpoint) for i in intents} == {
            ("add", _endpoint(1)),
            ("add", _endpoint(2)),
        }
        assert set(state.held("s1")) == {_endpoint(1).container_id, _endpoint(2).container_id}

    def test_a_repeat_announcement_programs_nothing(self) -> None:
        state = _state()
        announcement = Announcement("s1", _PEER, (_endpoint(1),), 1000.0)
        _deliver(state, announcement)
        assert _deliver(state, announcement, now=1001.0) == []

    def test_an_endpoint_that_stops_being_announced_is_withdrawn(self) -> None:
        """Nothing has to deliver a removal: absence from whole state IS the removal."""
        state = _state()
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1), _endpoint(2)), 1000.0))
        intents = _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1001.0))
        assert [(i.action, i.endpoint) for i in intents] == [("remove", _endpoint(2))]

    def test_removals_are_ordered_before_additions(self) -> None:
        """An endpoint that moved must have its old entry withdrawn before the new one lands, or
        the FDB carries two claims on one MAC."""
        state = _state(_PEER, "192.168.0.104")
        moved = _endpoint(1)
        _deliver(state, Announcement("s1", _PEER, (moved,), 1000.0))
        state.on_datagram(Announcement("s1", _PEER, (), 1001.0), now=1001.0)
        state.on_datagram(Announcement("s1", "192.168.0.104", (moved,), 1001.0), now=1001.0)
        assert [i.action for i in state.converge("s1")] == ["remove", "add"]

    def test_two_peers_are_held_apart(self) -> None:
        """An endpoint moves when its kernel is re-created on another node, and both nodes then
        name the same container. Replacing per sender is what makes the move converge."""
        state = _state(_PEER, "192.168.0.104")
        moved = _endpoint(1)
        _deliver(state, Announcement("s1", _PEER, (moved,), 1000.0))
        _deliver(state, Announcement("s1", "192.168.0.104", (moved,), 1001.0))
        _deliver(state, Announcement("s1", _PEER, (), 1002.0))
        assert state.held("s1") == {moved.container_id: (moved, "192.168.0.104")}

    def test_a_session_is_forgotten_whole(self) -> None:
        state = GossipState()
        state.on_membership("s1", [_PEER], now=900.0)
        state.on_membership("s2", [_PEER], now=900.0)
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1000.0))
        _deliver(state, Announcement("s2", _PEER, (_endpoint(2),), 1000.0))
        state.forget_session("s1")
        assert state.held("s1") == {}
        assert set(state.held("s2")) == {_endpoint(2).container_id}


class TestASnapshotIsAppliedWholeOrNotAtAll:
    """Applying each slice as it lands mixes snapshots: a receiver that took part 0 of the new one
    and part 1 of the old holds a state no sender ever had, and an endpoint deleted in the new one
    is re-installed from the old."""

    def _slices(self, endpoints: list[Endpoint], sent_at: float) -> list[Announcement]:
        out = []
        for datagram in announcements_for(
            "s1", _PEER, endpoints, sent_at=sent_at, key=_KEY, max_bytes=400
        ):
            announcement = decode(datagram, _KEY, now=sent_at)
            assert announcement is not None
            out.append(announcement)
        return out

    def test_slices_do_not_overwrite_each_other(self) -> None:
        state = _state()
        many = [_endpoint(n) for n in range(1, 12)]
        for announcement in self._slices(many, 1000.0):
            _deliver(state, announcement)
        assert set(state.held("s1")) == {e.container_id for e in many}

    def test_an_incomplete_snapshot_changes_nothing(self) -> None:
        """The sender re-announces whole state every interval, so waiting costs one interval.
        Adopting half of it costs a state no node ever held."""
        state = _state()
        many = [_endpoint(n) for n in range(1, 12)]
        slices = self._slices(many, 1000.0)
        assert len(slices) > 1
        for announcement in slices[:-1]:
            assert _deliver(state, announcement) == []
        assert state.held("s1") == {}

    def test_the_previous_snapshot_stands_while_the_next_assembles(self) -> None:
        state = _state()
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1000.0))
        for announcement in self._slices([_endpoint(n) for n in range(1, 12)], 1001.0)[:-1]:
            _deliver(state, announcement)
        assert set(state.held("s1")) == {_endpoint(1).container_id}

    def test_a_slice_of_an_older_snapshot_cannot_revive_a_deleted_endpoint(self) -> None:
        """The reordering this exists to stop: part 1 of the old snapshot arriving after the new
        one has been adopted would put back an endpoint the new one dropped."""
        state = _state()
        old = self._slices([_endpoint(n) for n in range(1, 12)], 1000.0)
        for announcement in old:
            _deliver(state, announcement)
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1001.0))
        assert _deliver(state, old[-1], now=1002.0) == []
        assert set(state.held("s1")) == {_endpoint(1).container_id}

    def test_a_half_assembled_snapshot_is_aged_out(self) -> None:
        state = _state()
        for announcement in self._slices([_endpoint(n) for n in range(1, 12)], 1000.0)[:-1]:
            state.on_datagram(announcement, now=1000.0)
        state.tick(now=1100.0, pending_ttl=15.0)
        assert state.converge("s1") == []
        assert state.held("s1") == {}


class TestWhatWasProgrammedIsKeptApartFromWhatWasSaid:
    """A failed `ip` call held as applied is indistinguishable from a successful one: the sender's
    next announcement is the same whole state, diffs to nothing, and the endpoint is never
    programmed again -- a peer's kernel unreachable for the life of the session."""

    def test_an_addition_that_failed_is_offered_again(self) -> None:
        state = _state()
        announcement = Announcement("s1", _PEER, (_endpoint(1),), 1000.0)
        state.on_datagram(announcement, now=1000.0)
        assert len(state.converge("s1")) == 1
        state.confirm("s1", applied=[])  # the host could not program it
        assert [(i.action, i.endpoint) for i in state.converge("s1")] == [("add", _endpoint(1))]

    def test_a_removal_that_failed_is_offered_again(self) -> None:
        """The half that used to be swallowed: a withdrawal that did not take leaves an FDB entry
        pointing at a kernel that is gone, for the life of the session."""
        state = _state()
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1000.0))
        state.on_datagram(Announcement("s1", _PEER, (), 1001.0), now=1001.0)
        removals = state.converge("s1")
        assert [i.action for i in removals] == ["remove"]
        state.confirm("s1", applied=[])  # the host could not unprogram it
        assert [(i.action, i.endpoint) for i in state.converge("s1")] == [("remove", _endpoint(1))]

    def test_only_the_confirmed_half_settles(self) -> None:
        state = _state()
        state.on_datagram(
            Announcement("s1", _PEER, (_endpoint(1), _endpoint(2)), 1000.0), now=1000.0
        )
        intents = state.converge("s1")
        state.confirm("s1", applied=[i for i in intents if i.endpoint == _endpoint(1)])
        assert [(i.action, i.endpoint) for i in state.converge("s1")] == [("add", _endpoint(2))]


class TestHealth:
    def test_silence_is_reported_but_is_not_a_withdrawal(self) -> None:
        """Withdrawing a quiet peer's kernels would cut a live session over a pause."""
        state = _state()
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1000.0))
        health = state.health("s1", now=1100.0, silent_after=30.0, expect_within=30.0)
        assert health.silent == frozenset({_PEER})
        assert set(state.held("s1")) == {_endpoint(1).container_id}

    def test_a_peer_never_heard_from_is_reported_separately(self) -> None:
        """A path that was never open is invisible to a silence check: there is no last-heard time
        to age, so the session reads as healthy while holding no remote endpoints at all."""
        state = _state(now=1000.0)
        health = state.health("s1", now=1100.0, silent_after=30.0, expect_within=30.0)
        assert health.never_heard == frozenset({_PEER})
        assert health.silent == frozenset()

    def test_a_peer_is_given_time_to_say_something_first(self) -> None:
        state = _state(now=1000.0)
        health = state.health("s1", now=1010.0, silent_after=30.0, expect_within=30.0)
        assert health.never_heard == frozenset()


class TestWhatANodeAnnouncesAboutItself:
    """Built from the addresses the privnet validated at attach, not from the attach plan. The
    plan keeps the overlay address inside its CNI config rather than on the spec, so reading it
    there found nothing: measured on three nodes, every announcement went out with an empty
    endpoint list and no peer's FDB was ever programmed by the exchange, while on the wire it
    looked exactly like a node holding no kernels."""

    def test_an_attached_container_is_announced(self) -> None:
        out = endpoints_of({"c1": "10.128.2.4"}, mac_of=mac_for_ip)
        assert [(e.container_id, e.ip, e.mac) for e in out] == [
            ("c1", "10.128.2.4", mac_for_ip("10.128.2.4"))
        ]

    def test_the_mac_is_the_one_a_peer_must_program(self) -> None:
        """Derived from the address, exactly as the attach derives the one it pins the NIC to."""
        (only,) = endpoints_of({"c1": "10.128.2.4"}, mac_of=mac_for_ip)
        assert only.mac == mac_for_ip("10.128.2.4")

    def test_names_are_attached_where_known(self) -> None:
        (only,) = endpoints_of({"c1": "10.128.2.4"}, mac_of=mac_for_ip, hostnames={"c1": "sub1"})
        assert only.cluster_hostname == "sub1"

    def test_a_node_holding_nothing_announces_an_empty_table(self) -> None:
        """Which is a real statement -- it withdraws this node's last kernel from every peer."""
        assert endpoints_of({}, mac_of=mac_for_ip) == []


class TestNamesTravelWithAddresses:
    """The session's cluster names (`main1`, `sub1`, ...) are what a kernel dials its peers by.
    Carrying them here is what lets a node answer for a peer's kernel without reading anything
    that peer wrote: the name and the address arrive together, from the node holding both."""

    def test_a_name_survives_the_round_trip(self) -> None:
        sent = Announcement("s1", _VTEP, (_endpoint(1),), sent_at=1000.0)
        got = decode(sent.encode(_KEY), _KEY, now=1000.0)
        assert got is not None and got.endpoints[0].cluster_hostname == "sub1"

    def test_a_nameless_endpoint_is_still_announced(self) -> None:
        """A kernel with no cluster name is unresolvable by name, not unreachable by address."""
        nameless = Endpoint(container_id="a" * 64, ip="10.128.2.9", mac="02:42:0a:80:02:09")
        got = decode(
            Announcement("s1", _VTEP, (nameless,), sent_at=1000.0).encode(_KEY), _KEY, now=1000.0
        )
        assert got is not None and got.endpoints == (nameless,)

    def test_a_name_of_the_wrong_type_drops_only_that_entry(self) -> None:
        body = json.dumps({
            "v": PROTOCOL_VERSION,
            "s": "s1",
            "t": _VTEP,
            "e": [_endpoint(1).to_wire(), {**_endpoint(2).to_wire(), "h": ["sub2"]}],
            "at": 1000.0,
            "p": 0,
            "n": 1,
        })
        got = decode(_sign(body.encode(), _KEY) + b"." + body.encode(), _KEY, now=1000.0)
        assert got is not None and got.endpoints == (_endpoint(1),)

    def test_a_rename_is_answered_without_touching_the_data_plane(self) -> None:
        """The name has to register, or every peer keeps answering the old one. It must not
        register as a removal: the container is still there, and withdrawing it would delete the
        FDB entry that is about to be re-added under the same MAC."""
        state = _state()
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1000.0))
        renamed = Endpoint(
            container_id=_endpoint(1).container_id,
            ip=_endpoint(1).ip,
            mac=_endpoint(1).mac,
            cluster_hostname="main1",
        )
        assert _deliver(state, Announcement("s1", _PEER, (renamed,), 1001.0)) == []
        assert state.held("s1")[renamed.container_id] == (renamed, _PEER)

    def test_an_address_change_does_touch_the_data_plane(self) -> None:
        """The other side of the same rule: a new address is a new FDB entry, and the old one has
        to go or the MAC is claimed twice."""
        state = _state()
        _deliver(state, Announcement("s1", _PEER, (_endpoint(1),), 1000.0))
        moved = Endpoint(
            container_id=_endpoint(1).container_id,
            ip="10.128.2.77",
            mac="02:42:0a:80:02:4d",
            cluster_hostname="sub1",
        )
        intents = _deliver(state, Announcement("s1", _PEER, (moved,), 1001.0))
        assert [(i.action, i.endpoint.ip) for i in intents] == [
            ("remove", _endpoint(1).ip),
            ("add", moved.ip),
        ]


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


class TestTheDeliveryOrderCannotChangeTheOutcome:
    """The property the whole machine exists for, and the one no test could reach while state and
    I/O were the same object: a datagram may be lost, reordered, duplicated or replayed, and what
    a receiver ends up holding is still exactly what its peer announced.

    This is the shape of the defect that only hardware found -- a slice of an older snapshot
    landing after a newer one and re-installing an endpoint that had been deleted.
    """

    def _snapshot(self, endpoints: list[Endpoint], sent_at: float) -> list[Announcement]:
        out = []
        for datagram in announcements_for(
            "s1", _PEER, endpoints, sent_at=sent_at, key=_KEY, max_bytes=400
        ):
            announcement = decode(datagram, _KEY, now=sent_at)
            assert announcement is not None
            out.append(announcement)
        return out

    @pytest.mark.parametrize("seed", range(25))
    def test_any_order_of_one_snapshot_converges_on_it(self, seed: int) -> None:
        endpoints = [_endpoint(n) for n in range(1, 12)]
        slices = self._snapshot(endpoints, 1000.0)
        shuffled = list(slices)
        random.Random(seed).shuffle(shuffled)

        state = _state()
        for announcement in shuffled:
            _deliver(state, announcement, now=1000.0)

        assert set(state.held("s1")) == {e.container_id for e in endpoints}

    @pytest.mark.parametrize("seed", range(25))
    def test_two_snapshots_interleaved_converge_on_the_newer(self, seed: int) -> None:
        """Every slice of both, in any order at all. The older one may arrive entirely after the
        newer and must still not put back what the newer dropped."""
        first = [_endpoint(n) for n in range(1, 12)]
        second = [_endpoint(1), _endpoint(2)]
        datagrams = self._snapshot(first, 1000.0) + self._snapshot(second, 1001.0)
        shuffled = list(datagrams)
        random.Random(seed).shuffle(shuffled)

        state = _state()
        for announcement in shuffled:
            _deliver(state, announcement, now=1002.0)

        # Every slice of both arrives, so the newer one is always adopted in the end -- whether it
        # completed first (the older is then too old to be looked at) or last (its slices held the
        # older ones out while it assembled).
        assert set(state.held("s1")) == {e.container_id for e in second}

    @pytest.mark.parametrize("seed", range(25))
    def test_duplicates_and_replays_change_nothing(self, seed: int) -> None:
        endpoints = [_endpoint(n) for n in range(1, 12)]
        slices = self._snapshot(endpoints, 1000.0)
        rng = random.Random(seed)
        noisy = [a for a in slices for _ in range(rng.randint(1, 3))]
        rng.shuffle(noisy)

        state = _state()
        for announcement in noisy:
            _deliver(state, announcement, now=1000.0)
        settled = state.converge("s1")

        assert settled == []
        assert set(state.held("s1")) == {e.container_id for e in endpoints}

    @pytest.mark.parametrize("seed", range(25))
    def test_a_host_that_keeps_failing_keeps_being_asked(self, seed: int) -> None:
        """Nothing is recorded as applied until it was, so the debt survives any number of passes
        and is settled the moment the host stops failing."""
        endpoints = [_endpoint(n) for n in range(1, 6)]
        rng = random.Random(seed)
        state = _state()
        state.on_datagram(Announcement("s1", _PEER, tuple(endpoints), 1000.0), now=1000.0)

        for _ in range(5):
            intents = state.converge("s1")
            state.confirm("s1", applied=[i for i in intents if rng.random() < 0.5])

        while intents := state.converge("s1"):
            state.confirm("s1", applied=intents)
        assert state.converge("s1") == []
        assert set(state.held("s1")) == {e.container_id for e in endpoints}
