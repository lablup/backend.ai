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
    PeerEndpoints,
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

#: How long a peer may be silent before it is reported. Never acted on -- see
#: `PeerEndpoints.forget_peer` for why silence is not a withdrawal.
SILENCE_REPORT_SEC: Final = 30.0


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

    async def gossip_program(
        self,
        session_id: str,
        *,
        add: Sequence[tuple[Endpoint, str]],
        remove: Sequence[tuple[Endpoint, str]],
    ) -> None:
        """Program (or unprogram) a peer's endpoints, each with the VTEP that announced it."""
        ...


class EndpointGossip:
    """One node's participation in every session's endpoint exchange."""

    _host: GossipHost
    _vtep: str
    _port: int
    _interval: float
    _held: PeerEndpoints
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
        self._held = PeerEndpoints()
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
                self.announce_all()
            except asyncio.CancelledError:
                raise
            except Exception:
                # One bad session must not end the timer for the rest: without it every other
                # session on this node stops re-announcing and its peers keep whatever they last
                # heard, forever.
                log.exception("the endpoint announce pass raised")

    def announce_all(self) -> None:
        for session_id in list(self._host.gossip_sessions()):
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
        added, removed = self._held.apply(announcement, now=time.time())
        if not added and not removed:
            return
        await self._host.gossip_program(
            announcement.session_id,
            add=[(e, announcement.vtep) for e in sorted(added, key=lambda e: e.container_id)],
            remove=[(e, announcement.vtep) for e in sorted(removed, key=lambda e: e.container_id)],
        )

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

    async def forget_session(self, session_id: str) -> None:
        """Drop everything held for a session this node no longer carries."""
        self._held.forget_session(session_id)
        self._known_peers.pop(session_id, None)

    async def drop_departed_peers(self, session_id: str) -> None:
        """Unprogram peers the session's membership no longer names.

        A node leaving is the manager's statement, and this is where it takes effect. It cannot
        come from silence: a peer that has merely paused would have its live kernels cut.
        """
        current = set(peers_to_notify(self._host.gossip_peers(session_id), self._vtep))
        departed = self._known_peers.get(session_id, set()) - current
        self._known_peers[session_id] = current
        for vtep in sorted(departed):
            gone = self._held.forget_peer(session_id, vtep)
            if gone:
                await self._host.gossip_program(
                    session_id,
                    add=[],
                    remove=[(e, vtep) for e in sorted(gone, key=lambda e: e.container_id)],
                )

    def problems(self) -> dict[str, str]:
        """Peers a session still names that have gone quiet, for the readiness surface.

        Not a failure of this node, and nothing is withdrawn over it -- but a peer whose privnet
        is wedged or unreachable has kernels that are about to be unreachable too, and nothing
        else on this node would say so.
        """
        now = time.time()
        out: dict[str, str] = {}
        for session_id in self._host.gossip_sessions():
            silent = self._held.silent_peers(
                session_id, now=now, older_than=SILENCE_REPORT_SEC
            ) & self._known_peers.get(session_id, set())
            if silent:
                out[f"gossip:{session_id}"] = (
                    f"no endpoint announcement in {SILENCE_REPORT_SEC:.0f}s from "
                    + ", ".join(sorted(silent))
                )
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
