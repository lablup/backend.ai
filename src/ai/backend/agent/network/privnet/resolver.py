"""Cluster name resolver for the privnet (BEP-1062).

containerd/runc gives a container no cluster DNS, so peers are resolved today from a static
``/etc/hosts`` the agent writes per kernel. This module is the dynamic replacement: the privnet
answers DNS for a session's cluster hostnames on the gateway address it already owns — a
**split-horizon** resolver that answers cluster names from a decentralized source (etcd-backed) and
**forwards everything else** to the node's upstream resolver. A peer whose address changes updates
one source entry and the next query sees it; the same resolution path serves every backend. See
``proposals/BEP-1062/cluster-name-resolution.md``.

Only the resolve logic and DNS wire handling live here (built on ``dnspython`` — the protocol is
not reimplemented). The name source (etcd) and the daemon wiring (which gateway to bind,
``/etc/resolv.conf``) are the caller's.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, Protocol, cast, override

import dns.asyncquery
import dns.exception
import dns.flags
import dns.message
import dns.rcode
import dns.rdataclass
import dns.rdatatype
import dns.rrset

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Short TTL: a cluster membership change (a restarted/moved kernel re-publishing its address) must
# reach peers quickly. The cost is more queries, bounded by the resolver's own etcd-watch cache.
_DEFAULT_TTL = 5
_DEFAULT_FORWARD_TIMEOUT = 3.0
_DNS_PORT = 53


class ClusterNameSource(Protocol):
    """Resolves a bare cluster hostname (e.g. ``sub1``) to its IPv4 address, or ``None`` when the
    name is not one this session owns. Implemented over the control-plane etcd view."""

    def resolve_name(self, hostname: str) -> str | None: ...


Forwarder = Callable[[dns.message.Message], Awaitable[dns.message.Message]]


def make_upstream_forwarder(
    upstreams: Sequence[str], *, timeout: float = _DEFAULT_FORWARD_TIMEOUT
) -> Forwarder:
    """A forwarder that relays a query to the first upstream that answers.

    On total failure it returns ``SERVFAIL`` (not ``NXDOMAIN``): a definitive "does not exist" would
    stop the client from trying the next configured nameserver, whereas ``SERVFAIL`` lets it retry.
    """

    async def forward(query: dns.message.Message) -> dns.message.Message:
        last_exc: Exception | None = None
        for server in upstreams:
            try:
                return await dns.asyncquery.udp(query, server, timeout=timeout)
            except (dns.exception.Timeout, OSError) as e:
                last_exc = e
        resp = dns.message.make_response(query)
        resp.set_rcode(dns.rcode.SERVFAIL)
        if last_exc is not None:
            log.debug(
                "cluster resolver: all upstreams failed a forwarded query: {}", repr(last_exc)
            )
        return resp

    return forward


class ClusterResolver:
    """Split-horizon resolver: cluster names → ``ClusterNameSource``; everything else → upstream.

    Authoritative for the names the source owns — it answers ``A`` and returns authoritative NODATA
    (an empty ``NOERROR``) for any other record type of a known name, so a client does not chase a
    name we own upstream. A name the source does not own is forwarded verbatim.
    """

    _names: ClusterNameSource
    _forward: Forwarder
    _ttl: int

    def __init__(
        self, names: ClusterNameSource, forward: Forwarder, *, ttl: int = _DEFAULT_TTL
    ) -> None:
        self._names = names
        self._forward = forward
        self._ttl = ttl

    async def resolve(self, query: dns.message.Message) -> dns.message.Message:
        # Only single-question IN queries can name a cluster host; anything else is not ours to
        # interpret, so let the upstream resolver handle it.
        if len(query.question) != 1:
            return await self._forward(query)
        question = query.question[0]
        if question.rdclass != dns.rdataclass.IN:
            return await self._forward(query)
        hostname = question.name.to_text(omit_final_dot=True).lower()
        ip = self._names.resolve_name(hostname)
        if ip is None:
            return await self._forward(query)
        resp = dns.message.make_response(query)
        resp.flags |= dns.flags.AA
        if question.rdtype == dns.rdatatype.A:
            resp.answer.append(dns.rrset.from_text(question.name, self._ttl, "IN", "A", ip))
        return resp


class _ResolverProtocol(asyncio.DatagramProtocol):
    """asyncio glue: parse each datagram, resolve it (concurrently — a forwarded query must not
    block others), and send the wire response back."""

    def __init__(self, resolver: ClusterResolver) -> None:
        self._resolver = resolver
        self._transport: asyncio.DatagramTransport | None = None
        self._pending: set[asyncio.Task[None]] = set()

    @override
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._transport = cast(asyncio.DatagramTransport, transport)

    @override
    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        task = asyncio.ensure_future(self._handle(data, addr))
        self._pending.add(task)
        task.add_done_callback(self._pending.discard)

    async def _handle(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        try:
            query = dns.message.from_wire(data)
        except dns.exception.DNSException:
            return  # not a parseable DNS query; drop silently as a resolver does
        try:
            resp = await self._resolver.resolve(query)
        except Exception:
            log.exception("cluster resolver: failed to resolve a query")
            resp = dns.message.make_response(query)
            resp.set_rcode(dns.rcode.SERVFAIL)
        if self._transport is not None:
            self._transport.sendto(resp.to_wire(), addr)


class ClusterDNSServer:
    """A per-node cluster DNS listener bound to a gateway address the privnet owns.

    ``start`` binds UDP ``bind_host:port``; ``stop`` closes it. TCP is intentionally omitted — an
    ``A`` answer for one hostname fits a UDP datagram; large-response TCP fallback is future work.
    """

    _resolver: ClusterResolver
    _bind_host: str
    _port: int
    _transport: asyncio.DatagramTransport | None

    def __init__(self, resolver: ClusterResolver, bind_host: str, *, port: int = _DNS_PORT) -> None:
        self._resolver = resolver
        self._bind_host = bind_host
        self._port = port
        self._transport = None

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _ResolverProtocol(self._resolver),
            local_addr=(self._bind_host, self._port),
        )
        self._transport = transport
        log.info("cluster DNS resolver listening on {}:{}", self._bind_host, self._port)

    async def stop(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None
