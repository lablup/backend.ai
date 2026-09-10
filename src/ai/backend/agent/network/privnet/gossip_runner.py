"""Drives endpoint announcements between privnets: when to send, where, and what to do on receipt.

`gossip.py` is the wire and the convergence rules and knows nothing about sockets or sessions.
This is the half that owns a UDP endpoint and a timer, and it reaches back into the privnet for
the four things it cannot know: which sessions exist, who their peers are, what this node holds,
and how to program what a peer says it holds.

Split that way because the rules are the part worth testing exhaustively and a socket makes that
awkward. `GossipHost` is the whole of what this needs from the daemon, so a test drives the real
timer and the real datagrams over a pair of fakes.

Sending is best-effort by construction. An announcement is whole state, so a datagram that does
not arrive is corrected by the next one; there is nothing to retry and nothing to acknowledge.
That is what lets this be UDP and lets a send failure be a log line rather than a session failure.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import socket
import time
from collections.abc import Sequence
from typing import Any, Final, Protocol, override

from ai.backend.agent.network.privnet.gossip import (
    Announcement,
    Endpoint,
    GossipState,
    Intent,
    announcements_for,
    decode,
    peers_to_notify,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: The default UDP port privnets announce on. Distinct from the VXLAN data port (4789) and from
#: swarm's own control plane (7946), so a node can run this beside either.
DEFAULT_GOSSIP_PORT: Final = 7947

#: How often every session re-announces, whether or not anything changed.
#:
#: This is the whole retry story. A datagram lost, a peer that was restarting, a node that joined
#: between two announcements -- each costs one interval and is then corrected, because what
#: arrives is whole state rather than a change the receiver had to already agree about.
ANNOUNCE_INTERVAL_SEC: Final = 5.0

#: How long a peer may be silent before it is reported. Never acted on -- only the manager's
#: membership withdraws a peer, because a node that has merely paused would have its kernels cut.
SILENCE_REPORT_SEC: Final = 30.0

#: How long after the membership first names a peer before never having heard from it is a
#: problem. A path that was never open -- a firewall, a route -- is invisible to the silence check
#: above, which has no last-heard time to age.
FIRST_CONTACT_SEC: Final = 30.0

#: How long a snapshot may sit half-assembled before its slices are discarded. The sender
#: re-announces whole state every interval, so a snapshot older than a few of them is superseded.
PENDING_SNAPSHOT_TTL_SEC: Final = ANNOUNCE_INTERVAL_SEC * 3


class GossipHost(Protocol):
    """What the runner needs from the privnet, and nothing else."""

    def gossip_key(self) -> str | None:
        """The key announcements are signed under, or None while this node has none.

        Cluster-wide, the same one the overlay's ESP uses: ESP policies select on the outer packet,
        which carries no session id, so there is one key for the cluster rather than one per
        session. A node that holds it can already inject and read overlay traffic, so signing with
        it adds no trust that was not already assumed -- what it stops is anything that does NOT
        hold it, which is every other host that can reach the port.
        """
        ...

    def gossip_sessions(self) -> Sequence[str]:
        """Sessions whose data plane this node currently carries."""
        ...

    def gossip_peers(self, session_id: str) -> Sequence[str]:
        """The VTEPs of that session's other members, as the manager published them."""
        ...

    def gossip_local_endpoints(self, session_id: str) -> Sequence[Endpoint]:
        """The overlay addresses this node holds for that session.

        This node assigned or validated every one of them itself, which is what makes it the only
        process entitled to announce them.
        """
        ...

    def gossip_generation(self, session_id: str) -> str | None:
        """Which incarnation of the session id this node is serving, if the manager publishes one."""
        ...

    async def gossip_program(self, session_id: str, intents: Sequence[Intent]) -> Sequence[Intent]:
        """Apply the intents in order, and return the ones that did not take.

        Returned rather than raised: one endpoint that will not program must not take the rest of
        the pass with it, and the caller records only what succeeded -- an intent left out of the
        confirmation is re-offered by the next convergence.
        """
        ...


class EndpointGossip:
    """One node's participation in every session's endpoint exchange."""

    _host: GossipHost
    _vtep: str
    _port: int
    _interval: float
    _state: GossipState
    _transport: asyncio.DatagramTransport | None
    _task: asyncio.Task[None] | None
    #: Sessions whose peers were last seen, so a member that leaves can be unprogrammed. The
    #: manager's membership is the authority on this; silence never is.
    _known_peers: dict[str, set[str]]

    def __init__(
        self,
        host: GossipHost,
        *,
        vtep: str,
        port: int = DEFAULT_GOSSIP_PORT,
        interval: float = ANNOUNCE_INTERVAL_SEC,
    ) -> None:
        self._host = host
        self._vtep = vtep
        self._port = port
        self._interval = interval
        self._state = GossipState()
        self._transport = None
        self._task = None
        self._known_peers = {}

    async def start(self) -> None:
        """Bind the announce port and begin the timer.

        Bound to the VTEP address rather than every interface: this is a control plane between
        nodes that already reach each other's tunnel endpoints, and there is no reason for it to
        answer on an interface the overlay does not use.
        """
        loop = asyncio.get_running_loop()
        transport, _protocol = await loop.create_datagram_endpoint(
            lambda: _Receiver(self),
            local_addr=(self._vtep, self._port),
            family=socket.AF_INET,
            reuse_port=False,
        )
        self._transport = transport
        self._task = asyncio.create_task(self._announce_periodically())
        log.info("endpoint gossip listening on {}:{}", self._vtep, self._port)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._transport is not None:
            self._transport.close()
            self._transport = None

    async def _announce_periodically(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._interval)
                await self.sweep()
            except asyncio.CancelledError:
                raise
            except Exception:
                # One bad session must not end the timer for the rest: without it every other
                # session on this node stops re-announcing and its peers keep whatever they last
                # heard, forever.
                log.exception("the endpoint announce pass raised")

    async def sweep(self) -> None:
        """One pass: settle who the peers are, then say what this node holds.

        The membership check runs here rather than where the manager's change lands, because every
        path that records a membership change is already holding that session's lock and
        unprogramming takes it again. A departed peer is therefore unprogrammed within an interval
        rather than instantly, which is the same latency every other part of this exchange has.
        """
        self._state.tick(now=time.time(), pending_ttl=PENDING_SNAPSHOT_TTL_SEC)
        for session_id in list(self._host.gossip_sessions()):
            await self.sync_membership(session_id)
            self.announce(session_id)

    def announce(self, session_id: str) -> None:
        """Send this node's whole state for one session to that session's peers.

        Called on the timer and again whenever what this node holds changes, so a peer learns
        about a new kernel in the time a datagram takes rather than at the next interval.
        """
        key = self._host.gossip_key()
        if key is None:
            return
        peers = peers_to_notify(self._host.gossip_peers(session_id), self._vtep)
        self._known_peers[session_id] = set(peers)
        if not peers:
            return
        datagrams = announcements_for(
            session_id,
            self._vtep,
            self._host.gossip_local_endpoints(session_id),
            sent_at=time.time(),
            generation=self._host.gossip_generation(session_id),
            key=key,
        )
        transport = self._transport
        if transport is None:
            return
        for peer in peers:
            for datagram in datagrams:
                try:
                    transport.sendto(datagram, (peer, self._port))
                except OSError as e:
                    # Best-effort by construction: whole state means the next interval corrects
                    # this, so a peer that is briefly unreachable is not a session failure.
                    log.debug("could not announce to {}: {}", peer, e)

    async def on_datagram(self, data: bytes, addr: tuple[str, int]) -> None:
        key = self._host.gossip_key()
        if key is None:
            return
        announcement = decode(data, key)
        if announcement is None:
            return
        if announcement.session_id not in set(self._host.gossip_sessions()):
            # Not a session this node carries. Not an error -- a peer may still be announcing a
            # session this node has already torn down.
            return
        if not self._is_current(announcement):
            return
        session_id = announcement.session_id
        now = time.time()
        # Refreshed here, not only on the timer: a peer the manager has just added would otherwise
        # have its first announcements dropped for want of state, costing an interval for nothing.
        # The membership still authorizes -- a sender it does not name gets no state and no
        # transition, whatever key signed the datagram.
        self._state.on_membership(session_id, self._host.gossip_peers(session_id), now=now)
        self._state.on_datagram(announcement, now=now)
        await self._converge(session_id)

    def _is_current(self, announcement: Announcement) -> bool:
        """Whether the announcement is about the incarnation this node is serving.

        A session id is reused. An announcement from the previous incarnation names addresses the
        live one does not hold, and programming them points this node's FDB at a kernel that is
        gone. Where neither side publishes a generation there is nothing to tell apart, which is
        the single-node and pre-field case.
        """
        mine = self._host.gossip_generation(announcement.session_id)
        if mine is None or announcement.generation is None:
            return True
        if mine == announcement.generation:
            return True
        log.debug(
            "ignoring an endpoint announcement for session {} from {}: it names incarnation {},"
            " this node serves {}",
            announcement.session_id,
            announcement.vtep,
            announcement.generation,
            mine,
        )
        return False

    def forget(self, session_id: str) -> None:
        """Drop everything held for a session this node no longer carries.

        Nothing is unprogrammed: the session's devices are going or gone, and what was programmed
        against them goes with them. This only stops the exchange from diffing a later session
        that reuses the id against a stranger's table.
        """
        self._state.forget_session(session_id)
        self._known_peers.pop(session_id, None)

    async def sync_membership(self, session_id: str) -> None:
        """Bring the peer set in line with the manager's membership, and settle what that changes.

        A node leaving is the manager's statement, and this is where it takes effect. It cannot
        come from silence: a peer that has merely paused would have its live kernels cut. A
        departed peer's endpoints leave the desired state, and the convergence below unprograms
        exactly them.
        """
        current = set(peers_to_notify(self._host.gossip_peers(session_id), self._vtep))
        self._known_peers[session_id] = current
        self._state.on_membership(session_id, current, now=time.time())
        await self._converge(session_id)

    async def _converge(self, session_id: str) -> None:
        """Ask the host for the difference, and record only what it confirms.

        Anything the host could not program is simply left out of the confirmation, so it is still
        a difference on the next pass. There is no retry list to keep and none to lose.
        """
        intents = self._state.converge(session_id)
        if not intents:
            return
        failed = set(await self._host.gossip_program(session_id, intents))
        self._state.confirm(session_id, applied=[i for i in intents if i not in failed])

    def cluster_names(self, session_id: str) -> dict[str, str]:
        """``{cluster_hostname: ip}`` for what this session's PEERS have announced.

        Lower-cased, because the resolver answering from it is answering DNS. The local half is
        the caller's -- this object only ever holds what other nodes said.
        """
        return {
            endpoint.cluster_hostname.lower(): endpoint.ip
            for endpoint, _vtep in self._state.held(session_id).values()
            if endpoint.cluster_hostname
        }

    def problems(self) -> dict[str, str]:
        """Peers a session names that are not saying what they should, for the readiness surface.

        Two shapes, reported apart because they point at different faults. A peer heard once and
        now quiet is a privnet that is wedged or a node that went away. A peer never heard from at
        all is more often a path that was never open, and a silence check cannot see it: there is
        no last-heard time to age.
        """
        now = time.time()
        out: dict[str, str] = {}
        for session_id in self._host.gossip_sessions():
            health = self._state.health(
                session_id,
                now=now,
                silent_after=SILENCE_REPORT_SEC,
                expect_within=FIRST_CONTACT_SEC,
            )
            reasons: list[str] = []
            if health.never_heard:
                reasons.append(
                    f"no endpoint announcement ever from {', '.join(sorted(health.never_heard))}"
                    f" ({FIRST_CONTACT_SEC:.0f}s after the session named them)"
                )
            if health.silent:
                reasons.append(
                    f"no endpoint announcement in {SILENCE_REPORT_SEC:.0f}s from "
                    + ", ".join(sorted(health.silent))
                )
            if reasons:
                out[f"gossip:{session_id}"] = "; ".join(reasons)
        return out


class _Receiver(asyncio.DatagramProtocol):
    #: Held for the life of each handler. A task nothing references can be collected while it is
    #: still waiting, and the announcement it was applying is then lost with no error anywhere --
    #: a peer's kernel silently never programmed until the next interval, or never at all if that
    #: one is dropped the same way.
    _handlers: set[asyncio.Task[None]]

    def __init__(self, gossip: EndpointGossip) -> None:
        self._gossip = gossip
        self._handlers = set()

    @override
    def datagram_received(self, data: bytes, addr: Any) -> None:
        # Handled on a task: applying an announcement programs devices, and blocking the
        # protocol's callback would stall every other datagram behind one slow `ip` call.
        task = asyncio.create_task(self._handle(data, addr))
        self._handlers.add(task)
        task.add_done_callback(self._handlers.discard)

    async def _handle(self, data: bytes, addr: Any) -> None:
        try:
            await self._gossip.on_datagram(data, addr)
        except Exception:
            log.exception("failed to apply an endpoint announcement from {}", addr)
