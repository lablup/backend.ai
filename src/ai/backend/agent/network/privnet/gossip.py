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
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

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
    #: Whole state is what makes a lost datagram cost one interval instead of a missing entry, and
    #: a node with more endpoints than fit one datagram cannot put its whole state in one. So the
    #: unit of "whole" is the SLICE: a receiver replaces what it holds for (sender, part), not for
    #: the sender outright. Splitting without this loses every slice but the last, because each
    #: would replace the one before it.
    #:
    #: `parts` travels too so a receiver can drop slices that no longer exist: a node that goes
    #: from three slices to one must not leave the other two programmed forever.
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


def decode(datagram: bytes, key: str, *, now: float | None = None) -> Announcement | None:
    """Parse and authenticate one announcement, or None with the reason logged at debug.

    Verified BEFORE parsing: an unauthenticated datagram is not input this daemon reasons about,
    it is noise from whoever can reach the port. The privnet holds CAP_NET_ADMIN, so the cheapest
    possible rejection is the right one.
    """
    signature, _, body = datagram.partition(b".")
    if not body:
        return None
    if not hmac.compare_digest(signature, _sign(body, key)):
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


class PeerEndpoints:
    """What every peer last said it holds, and what that means to program.

    Keyed by the announcing VTEP rather than by container: an endpoint moves when its kernel is
    re-created on another node, and both nodes then name the same container. Replacing per sender
    is what makes the move converge -- the old holder's next announcement no longer lists it, and
    the entry it left goes with that.
    """

    #: (session_id, vtep, part) -> what that node last announced in that slice, by container id.
    #: Per slice, not per sender: a node too big for one datagram sends several, and replacing per
    #: sender would leave only the last of them. See `Announcement.part`.
    _held: dict[tuple[str, str, int], dict[str, Endpoint]]
    #: (session_id, vtep) -> when. A peer that has stopped announcing is not the same as one that
    #: announced nothing, and only the second is a withdrawal.
    _heard_at: dict[tuple[str, str], float]

    def __init__(self) -> None:
        self._held = {}
        self._heard_at = {}

    def apply(
        self, announcement: Announcement, *, now: float
    ) -> tuple[set[Endpoint], set[Endpoint]]:
        """Record what a peer announced. Returns ``(to_add, to_remove)`` for this sender.

        Both are computed against what that same sender said last, so a caller programs only the
        difference -- the whole point of announcing whole state is that the receiver, not the
        network, works out what changed.
        """
        session_id, vtep = announcement.session_id, announcement.vtep
        key = (session_id, vtep, announcement.part)
        previous = self._held.get(key, {})
        current = {e.container_id: e for e in announcement.endpoints}
        self._held[key] = current
        self._heard_at[(session_id, vtep)] = now
        added = {e for cid, e in current.items() if previous.get(cid) != e}
        removed = {e for cid, e in previous.items() if current.get(cid) != e}
        # A sender that shrank from three slices to one must not leave the other two programmed:
        # they are whole state for indices it no longer sends, so nothing would ever replace them.
        for stale in [
            k
            for k in self._held
            if k[0] == session_id and k[1] == vtep and k[2] >= announcement.parts
        ]:
            removed |= set(self._held.pop(stale).values())
        # An endpoint that merely moved between this sender's own slices is not a removal.
        still_held = {
            e.container_id
            for k, held in self._held.items()
            if k[0] == session_id and k[1] == vtep
            for e in held.values()
        }
        removed = {e for e in removed if e.container_id not in still_held}
        return added, removed

    def forget_peer(self, session_id: str, vtep: str) -> set[Endpoint]:
        """Drop a peer the session no longer names, returning what it had been holding.

        Called when the membership itself changes -- a node leaving is the manager's statement,
        not something silence can establish. Silence is a node that may simply be busy, and
        withdrawing its kernels' addresses on a timeout would cut a live session over a pause.
        """
        self._heard_at.pop((session_id, vtep), None)
        gone: set[Endpoint] = set()
        for key in [k for k in self._held if k[0] == session_id and k[1] == vtep]:
            gone |= set(self._held.pop(key).values())
        return gone

    def forget_session(self, session_id: str) -> None:
        for held_key in [k for k in self._held if k[0] == session_id]:
            self._held.pop(held_key, None)
        for heard_key in [k for k in self._heard_at if k[0] == session_id]:
            self._heard_at.pop(heard_key, None)

    def held(self, session_id: str) -> dict[str, tuple[Endpoint, str]]:
        """``{container_id: (endpoint, vtep)}`` across every peer of this session."""
        out: dict[str, tuple[Endpoint, str]] = {}
        for (sid, vtep, _part), endpoints in self._held.items():
            if sid != session_id:
                continue
            for container_id, endpoint in endpoints.items():
                out[container_id] = (endpoint, vtep)
        return out

    def silent_peers(self, session_id: str, *, now: float, older_than: float) -> set[str]:
        """Peers of this session that have not been heard from recently.

        Reported, never acted on here: see `forget_peer` for why silence is not a withdrawal. It
        is worth surfacing because a peer that has gone quiet while the manager still names it is
        a node whose privnet is wedged or unreachable, and its kernels are about to be
        unreachable too.
        """
        return {
            vtep
            for (sid, vtep), heard in self._heard_at.items()
            if sid == session_id and now - heard > older_than
        }


def peers_to_notify(peer_vteps: Sequence[str] | None, self_vtep: str) -> list[str]:
    """The peers one announcement goes to: the session's members, less this node.

    A node announcing to itself would program its own kernels' addresses against its own VTEP,
    which is a tunnel to nowhere -- the local ones are already attached to the bridge directly.
    """
    return sorted({vtep for vtep in (peer_vteps or ()) if vtep and vtep != self_vtep})


def endpoints_of(
    attached: Mapping[str, Any],
    *,
    overlay_role: Any,
    hostnames: Mapping[str, str] | None = None,
) -> list[Endpoint]:
    """This node's own endpoints for a session, read from what its attach recorded.

    The privnet assigned or validated every one of these itself, which is what makes it the right
    thing to announce: it is the only process that can say, of its own knowledge, which addresses
    this host holds. ``hostnames`` names them, so a peer can resolve the session's cluster names
    from the same announcement instead of from a table it would have to read somewhere else.
    """
    hostnames = hostnames or {}
    out: list[Endpoint] = []
    for container_id, plan in attached.items():
        for spec in getattr(plan, "attachments", ()):
            if getattr(spec, "role", None) is not overlay_role:
                continue
            ip = getattr(spec, "ip", None)
            args = getattr(spec, "cni_capability_args", None) or {}
            mac = args.get("mac") if isinstance(args, Mapping) else None
            if not ip or not mac:
                continue
            out.append(
                Endpoint(
                    container_id=container_id,
                    ip=str(ip),
                    mac=str(mac),
                    cluster_hostname=hostnames.get(container_id),
                )
            )
    return out
