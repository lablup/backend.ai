"""Endpoint propagation between the privileged network daemons of one session (BEP-1078).

Which node holds which container address is the one fact in this data plane that changes as fast
as containers do, and every node of a session needs it: an overlay peer is reached by programming
its MAC against its node's VTEP, so a kernel nobody was told about is a kernel nothing can reach.

It used to travel through etcd -- the manager wrote an ``endpoints/`` table and every agent watched
its session's subtree. That put the fastest-changing fact in the cluster's control-plane store, one
subscription per agent per session, and it handed the *unprivileged* agent a read channel on that
store. Docker Swarm, whose shape this data plane otherwise follows, deliberately splits the two:
Raft holds the allocation (subnet, VNI), and the daemons that own each host's networking gossip the
endpoints among themselves. This module is that half, between privnets.

What it is NOT is a membership protocol. Swarm needs one because nothing else tells a daemon who
its peers are; here the manager already publishes the session's members and the privnet already
keeps them (`PrivNetJournal.peers`). So there is no failure detector, no join/leave, no
anti-entropy tree -- only:

- **Whole state, not deltas.** An announcement carries every endpoint its sender has for a session.
  A receiver replaces what it holds for that sender. An endpoint that stops being announced is
  gone, so nothing has to deliver a removal, and a lost datagram costs one interval rather than a
  permanently missing entry.
- **A snapshot is applied whole or not at all.** A sender with more endpoints than fit one
  datagram sends several, all carrying the same `sent_at`. The receiver assembles them and adopts
  the result only once every slice is in, so it never holds a state made of two snapshots -- which
  is how an endpoint deleted in the newer one gets re-installed from the older.
- **Desired and applied are separate.** What a peer says is not what this node managed to
  program. The difference between them is the retry: nothing is recorded as applied until it was.
- **Idempotent application.** `add_endpoint`/`del_endpoint` already are; a repeat announcement
  programs nothing.
- **Authenticated by the session's own key.** The privnet's only input has until now been a 0600
  unix socket checked with SO_PEERCRED. This is the first that arrives from the network, so an
  announcement carries an HMAC under the session's encryption key -- the same one its ESP already
  uses -- and one that does not verify is dropped without being parsed further.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: Wire version. A receiver refuses what it does not know rather than guessing at the fields.
PROTOCOL_VERSION: Final = 1

#: How stale an announcement may be and still be applied. It bounds replay: a datagram captured
#: off the underlay cannot be re-injected later to restore an endpoint that has since moved. Wide
#: enough that ordinary clock skew between nodes does not drop live traffic, which would show up
#: as a peer that intermittently disappears.
MAX_AGE_SEC: Final = 60.0

#: The largest announcement that fits one datagram without fragmenting on a 1500-byte underlay.
#: More endpoints than that go in further datagrams -- see `part` for why each one is still whole
#: state, and of what.
MAX_PAYLOAD_BYTES: Final = 1200


@dataclass(frozen=True)
class Endpoint:
    """One container's overlay address, as the node holding it knows them."""

    container_id: str
    ip: str
    mac: str
    cluster_hostname: str | None = None

    def to_wire(self) -> dict[str, Any]:
        out: dict[str, Any] = {"c": self.container_id, "i": self.ip, "m": self.mac}
        if self.cluster_hostname:
            out["h"] = self.cluster_hostname
        return out

    @classmethod
    def from_wire(cls, raw: Any) -> Endpoint | None:
        """None for anything malformed. One bad entry must not discard a whole announcement: the
        rest of the sender's endpoints are still true, and dropping them would black-hole live
        kernels over a field this node does not understand."""
        if not isinstance(raw, dict):
            return None
        cid, ip, mac = raw.get("c"), raw.get("i"), raw.get("m")
        host = raw.get("h")
        if not (isinstance(cid, str) and isinstance(ip, str) and isinstance(mac, str)):
            return None
        if not cid or not ip or not mac:
            return None
        if host is not None and not isinstance(host, str):
            return None
        return cls(container_id=cid, ip=ip, mac=mac, cluster_hostname=host or None)


@dataclass(frozen=True)
class Announcement:
    """Every endpoint one node holds for one session, at one moment."""

    session_id: str
    #: The sender's tunnel endpoint. It is what a receiver programs each of these MACs against,
    #: and what says whose state this replaces -- never taken from the datagram's source address,
    #: which NAT or a second interface can make disagree with the tunnel.
    vtep: str
    endpoints: tuple[Endpoint, ...]
    #: Unix seconds at the sender. Bounds replay; see `MAX_AGE_SEC`.
    sent_at: float
    #: Which incarnation of the session id this is about, when the manager publishes one. A
    #: session id is reused, and an announcement from the previous incarnation names addresses the
    #: live one does not hold.
    generation: str | None = None
    #: Which slice of the sender's endpoints this datagram carries, and how many slices there are.
    #:
    #: A node with more endpoints than fit one datagram cannot put its whole state in one, so the
    #: state is sliced and every slice of one snapshot carries that snapshot's `sent_at`. `parts`
    #: is how a receiver knows when it has them all; until then the snapshot is not adopted, and
    #: the sender's previous one stays in force.
    part: int = 0
    parts: int = 1

    def encode(self, key: str) -> bytes:
        body = json.dumps(
            {
                "v": PROTOCOL_VERSION,
                "s": self.session_id,
                "t": self.vtep,
                "e": [e.to_wire() for e in self.endpoints],
                "at": self.sent_at,
                "p": self.part,
                "n": self.parts,
                **({"g": self.generation} if self.generation is not None else {}),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return _sign(body, key) + b"." + body


def _sign(body: bytes, key: str) -> bytes:
    return hmac.new(key.encode("utf-8"), body, hashlib.sha256).hexdigest().encode("ascii")


def decode(
    datagram: bytes, key: str | Iterable[str], *, now: float | None = None
) -> Announcement | None:
    """Parse and authenticate one announcement, or None with the reason logged at debug.

    Verified BEFORE parsing: an unauthenticated datagram is not input this daemon reasons about,
    it is noise from whoever can reach the port. The privnet holds CAP_NET_ADMIN, so the cheapest
    possible rejection is the right one.

    Several keys because one node can hold sessions created under different cluster roots -- a
    rotation gives later sessions a different key while the ones already running keep theirs, and
    both are this node's to verify. The candidates are the keys of the sessions it carries, so the
    set is one or two, and each costs one HMAC over at most a datagram.
    """
    keys = [key] if isinstance(key, str) else list(key)
    signature, _, body = datagram.partition(b".")
    if not body:
        return None
    if not any(hmac.compare_digest(signature, _sign(body, k)) for k in keys):
        return None
    try:
        raw = json.loads(body)
    except ValueError:
        return None
    if not isinstance(raw, dict) or raw.get("v") != PROTOCOL_VERSION:
        return None
    session_id, vtep, sent_at = raw.get("s"), raw.get("t"), raw.get("at")
    generation = raw.get("g")
    if not (isinstance(session_id, str) and session_id and isinstance(vtep, str) and vtep):
        return None
    if not isinstance(sent_at, (int, float)):
        return None
    if generation is not None and not isinstance(generation, str):
        return None
    if abs((time.time() if now is None else now) - float(sent_at)) > MAX_AGE_SEC:
        return None
    entries = raw.get("e")
    if not isinstance(entries, list):
        return None
    part, parts = raw.get("p", 0), raw.get("n", 1)
    if not (isinstance(part, int) and isinstance(parts, int)):
        return None
    if parts < 1 or not (0 <= part < parts):
        return None
    endpoints = tuple(e for e in (Endpoint.from_wire(item) for item in entries) if e is not None)
    return Announcement(
        session_id=session_id,
        vtep=vtep,
        endpoints=endpoints,
        sent_at=float(sent_at),
        generation=generation,
        part=part,
        parts=parts,
    )


def announcements_for(
    session_id: str,
    vtep: str,
    endpoints: Iterable[Endpoint],
    *,
    sent_at: float,
    generation: str | None = None,
    key: str,
    max_bytes: int = MAX_PAYLOAD_BYTES,
) -> list[bytes]:
    """Encode one node's endpoints for a session, split so each datagram fits the underlay.

    Always at least one datagram, even with no endpoints: "I hold none" is the message that
    withdraws this node's last kernel from every peer. Losing it to an empty-list shortcut is how
    a departed node's addresses stay programmed on its peers for the life of the session.
    """
    ordered = sorted(endpoints, key=lambda e: e.container_id)
    batches: list[list[Endpoint]] = [[]]
    for endpoint in ordered:
        candidate = [*batches[-1], endpoint]
        probe = Announcement(session_id, vtep, tuple(candidate), sent_at, generation).encode(key)
        if len(probe) > max_bytes and batches[-1]:
            batches.append([endpoint])
        else:
            batches[-1] = candidate
    # Always at least one, even empty: "I hold none" is the message that withdraws this node's
    # last kernel from every peer, and skipping it leaves those addresses programmed for good.
    return [
        Announcement(
            session_id, vtep, tuple(batch), sent_at, generation, part=index, parts=len(batches)
        ).encode(key)
        for index, batch in enumerate(batches)
    ]


def _fdb_identity(endpoint: Endpoint | None) -> tuple[str, str] | None:
    """What a peer's endpoint is to the data plane: one FDB and ARP entry, keyed by address and
    MAC. Everything else it carries -- the cluster name -- is answered from memory."""
    return None if endpoint is None else (endpoint.ip, endpoint.mac)


@dataclass(frozen=True)
class Intent:
    """One programming action the convergence asks for, and the peer it is on behalf of."""

    action: Literal["add", "remove"]
    endpoint: Endpoint
    vtep: str


@dataclass(frozen=True)
class SessionHealth:
    """What the exchange can say about one session's peers, for the readiness surface."""

    #: Peers the membership names that have never been heard from at all.
    never_heard: frozenset[str]
    #: Peers that were heard from once and have since gone quiet.
    silent: frozenset[str]


@dataclass
class _Pending:
    """A snapshot being assembled. Applied only once every slice of it has arrived."""

    sent_at: float
    parts: int
    slices: dict[int, tuple[Endpoint, ...]]
    started: float


@dataclass
class _Peer:
    """One peer's receive state for one session.

    Created by MEMBERSHIP, never by a datagram: a sender this session does not name has no state
    here, so there is no transition for it to drive. That is the admission rule, not a check.
    """

    expected_since: float
    heard_at: float | None = None
    #: The last snapshot received whole, by container id. None until one completes.
    snapshot: dict[str, Endpoint] | None = None
    #: The `sent_at` of that snapshot. Its identity and its order: slices of one snapshot carry
    #: the same value, and anything older than it is a datagram that lost a race.
    snapshot_at: float = 0.0
    pending: _Pending | None = None


class GossipState:
    """What peers have said they hold, what this node has actually programmed, and the difference.

    The two are separate on purpose. Held as one, a failed `ip` call is indistinguishable from a
    successful one -- the sender's next announcement is the same whole state, diffs to nothing,
    and the endpoint is never programmed again. Kept apart, the difference IS the retry: nothing
    is recorded as applied until it was, and the next convergence re-offers exactly the rest.
    """

    #: (session_id, vtep) -> that peer's receive state.
    _peers: dict[tuple[str, str], _Peer]
    #: session_id -> {(vtep, container_id): endpoint} that this node has programmed and confirmed.
    _applied: dict[str, dict[tuple[str, str], Endpoint]]

    def __init__(self) -> None:
        self._peers = {}
        self._applied = {}

    # --- inputs -------------------------------------------------------------------------------

    def on_membership(self, session_id: str, peer_vteps: Iterable[str], *, now: float) -> None:
        """Bring the peer set in line with what the manager published.

        A node leaving is the manager's statement, and this is the only thing that removes a peer.
        Silence never does: a peer that has merely paused would have its live kernels cut.
        """
        wanted = {vtep for vtep in peer_vteps if vtep}
        for vtep in wanted:
            self._peers.setdefault((session_id, vtep), _Peer(expected_since=now))
        for key in [k for k in self._peers if k[0] == session_id and k[1] not in wanted]:
            self._peers.pop(key)

    def on_datagram(self, announcement: Announcement, *, now: float) -> None:
        """Record one slice. A snapshot becomes this peer's state only once every slice is in.

        Applying a slice as it lands mixes snapshots: a receiver that took part 0 of the new one
        and part 1 of the old holds a state no sender ever had, and an endpoint deleted in the new
        one is re-installed from the old. Assembling first costs at most one interval when a
        datagram is lost -- the sender re-announces whole state anyway -- and cannot mix.
        """
        peer = self._peers.get((announcement.session_id, announcement.vtep))
        if peer is None:
            # No membership, no state, no transition. A sender this session does not name cannot
            # reach the programming path, whatever key it holds.
            return
        peer.heard_at = now
        if announcement.sent_at <= peer.snapshot_at:
            return
        pending = peer.pending
        if pending is None or announcement.sent_at > pending.sent_at:
            pending = _Pending(
                sent_at=announcement.sent_at, parts=announcement.parts, slices={}, started=now
            )
            peer.pending = pending
        elif announcement.sent_at < pending.sent_at:
            return
        pending.slices[announcement.part] = announcement.endpoints
        if len(pending.slices) < pending.parts:
            return
        peer.snapshot = {e.container_id: e for slice_ in pending.slices.values() for e in slice_}
        peer.snapshot_at = pending.sent_at
        peer.pending = None

    def tick(self, *, now: float, pending_ttl: float) -> None:
        """Discard snapshots that never completed, so a lost slice does not hold memory for good."""
        for peer in self._peers.values():
            if peer.pending is not None and now - peer.pending.started > pending_ttl:
                peer.pending = None

    def confirm(self, session_id: str, *, applied: Iterable[Intent]) -> None:
        """Record the intents that actually took. Anything left out stays owed.

        Called with what the host confirmed, never with what it was asked to do. That distinction
        is the whole reason the applied state is kept apart from the desired one.
        """
        state = self._applied.setdefault(session_id, {})
        for intent in applied:
            key = (intent.vtep, intent.endpoint.container_id)
            if intent.action == "add":
                state[key] = intent.endpoint
            else:
                state.pop(key, None)

    def forget_session(self, session_id: str) -> None:
        """Drop a session whole. Nothing is unprogrammed: its devices are going or gone."""
        for key in [k for k in self._peers if k[0] == session_id]:
            self._peers.pop(key)
        self._applied.pop(session_id, None)

    # --- outputs ------------------------------------------------------------------------------

    def desired(self, session_id: str) -> dict[tuple[str, str], Endpoint]:
        """``{(vtep, container_id): endpoint}`` this session's peers have announced whole."""
        out: dict[tuple[str, str], Endpoint] = {}
        for (sid, vtep), peer in sorted(self._peers.items()):
            if sid != session_id or peer.snapshot is None:
                continue
            for container_id, endpoint in peer.snapshot.items():
                out[(vtep, container_id)] = endpoint
        return out

    def converge(self, session_id: str) -> list[Intent]:
        """The difference between what peers say and what this node has programmed.

        Compared on what a peer's entry actually IS to the data plane -- its address and MAC --
        and not on the whole record. A kernel that is only renamed keeps the same FDB entry, and
        re-deriving it would delete the entry and re-add it under the same MAC for nothing, with a
        window in between where the kernel is unreachable.

        Removals first, for the reason the whole data plane orders them that way: an endpoint that
        moved must have its old entry withdrawn before the new one is installed, or the FDB
        carries two claims on one MAC.
        """
        desired = self.desired(session_id)
        applied = self._applied.get(session_id, {})
        removals = [
            Intent("remove", endpoint, vtep)
            for (vtep, cid), endpoint in sorted(applied.items())
            if _fdb_identity(desired.get((vtep, cid))) != _fdb_identity(endpoint)
        ]
        additions = [
            Intent("add", endpoint, vtep)
            for (vtep, cid), endpoint in sorted(desired.items())
            if _fdb_identity(applied.get((vtep, cid))) != _fdb_identity(endpoint)
        ]
        return removals + additions

    def held(self, session_id: str) -> dict[str, tuple[Endpoint, str]]:
        """``{container_id: (endpoint, vtep)}`` across every peer of this session.

        From what peers announced, not from what programming succeeded: a name that resolves to an
        address whose FDB entry is still owed is a peer that is briefly unreachable, while no
        answer at all is a peer that does not exist.
        """
        out: dict[str, tuple[Endpoint, str]] = {}
        for (vtep, container_id), endpoint in sorted(self.desired(session_id).items()):
            out[container_id] = (endpoint, vtep)
        return out

    def health(
        self, session_id: str, *, now: float, silent_after: float, expect_within: float
    ) -> SessionHealth:
        """Peers that are not saying what they should, in the two ways that differ.

        A peer heard once and now quiet may be wedged. A peer never heard at all is more often a
        path that was never open -- a firewall, a route -- and it is invisible to a silence check
        because there is no last-heard time to age.
        """
        never: set[str] = set()
        silent: set[str] = set()
        for (sid, vtep), peer in self._peers.items():
            if sid != session_id:
                continue
            if peer.heard_at is None:
                if now - peer.expected_since > expect_within:
                    never.add(vtep)
            elif now - peer.heard_at > silent_after:
                silent.add(vtep)
        return SessionHealth(never_heard=frozenset(never), silent=frozenset(silent))


def peers_to_notify(peer_vteps: Sequence[str] | None, self_vtep: str) -> list[str]:
    """The peers one announcement goes to: the session's members, less this node.

    A node announcing to itself would program its own kernels' addresses against its own VTEP,
    which is a tunnel to nowhere -- the local ones are already attached to the bridge directly.
    """
    return sorted({vtep for vtep in (peer_vteps or ()) if vtep and vtep != self_vtep})


def endpoints_of(
    overlay_ips: Mapping[str, str],
    *,
    mac_of: Callable[[str], str],
    hostnames: Mapping[str, str] | None = None,
) -> list[Endpoint]:
    """This node's own endpoints for a session, from the addresses its attach validated.

    Taken from the privnet's own record of what it assigned, not from the attach plan: the plan
    keeps the overlay address inside its CNI config rather than on the spec, so reading it there
    found nothing and this node announced an empty table -- every peer's FDB left unprogrammed by
    the exchange while it looked, on the wire, like a node that simply holds no kernels.

    The MAC is derived from the address, exactly as the attach derives the one it pins the NIC to,
    so what is announced is what a peer's FDB must carry. ``hostnames`` names them, so a peer can
    resolve the session's cluster names from the same announcement.
    """
    hostnames = hostnames or {}
    return [
        Endpoint(
            container_id=container_id,
            ip=ip,
            mac=mac_of(ip),
            cluster_hostname=hostnames.get(container_id),
        )
        for container_id, ip in sorted(overlay_ips.items())
    ]
