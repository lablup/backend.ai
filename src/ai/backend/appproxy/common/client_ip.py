"""Client IP allowlist matching and X-Forwarded-For resolution shared by the
coordinator (request validation, Traefik config generation) and the worker
(Python-mode enforcement).

The allowlist is persisted on a circuit as a comma-separated string of CIDR
blocks or bare IP addresses (``Circuit.allowed_client_ips``). A null/blank value
means the circuit is reachable from anywhere.
"""

import ipaddress
import logging
from collections.abc import Sequence

from aiohttp import web

from ai.backend.appproxy.common.errors import ClientIPNotAllowed
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

type IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network


class ClientIPValidator:
    """Per-circuit client-IP allowlist.

    Constructed from a circuit's ``allowed_client_ips`` string; the string is
    parsed once at construction and the resulting networks are held as a field,
    so repeated matching does not re-parse. An empty allowlist (``None``/blank,
    or every entry invalid) means "no restriction" — every client is allowed.
    """

    def __init__(self, allowed_client_ips: str | None) -> None:
        self._networks = self._parse(allowed_client_ips)

    @staticmethod
    def _parse(value: str | None) -> list[IPNetwork]:
        """Parse a comma-separated CIDR/IP allowlist into networks. Each entry is
        a bare IP (host route, ``/32`` or ``/128``) or a CIDR block; whitespace
        and empty entries are ignored. Invalid entries are logged and skipped, so
        one malformed entry never breaks enforcement for the rest."""
        if not value:
            return []
        networks: list[IPNetwork] = []
        for raw in value.split(","):
            entry = raw.strip()
            if not entry:
                continue
            try:
                networks.append(ipaddress.ip_network(entry, strict=False))
            except ValueError:
                log.exception("Skipping invalid entry in allowed_client_ips: {!r}", entry)
        return networks

    @property
    def is_restricted(self) -> bool:
        """Whether any allowlist entry is configured. ``False`` means every
        client is allowed."""
        return bool(self._networks)

    @property
    def ranges(self) -> list[str]:
        """Normalized CIDR strings, e.g. for Traefik ``ipAllowList`` /
        ``ClientIP`` rule generation."""
        return [str(net) for net in self._networks]

    def is_allowed(self, client_ip: str) -> bool:
        """Whether ``client_ip`` falls within any allowed network.

        An empty allowlist means no restriction, so every client is allowed. A
        ``client_ip`` that cannot be parsed is rejected (fail-closed).
        """
        if not self._networks:
            return True
        try:
            addr = ipaddress.ip_address(client_ip)
        except ValueError:
            return False
        return any(addr in net for net in self._networks)


class ClientIPResolver:
    """Resolves the effective client IP from ``X-Forwarded-For``, trusting the
    header only when the immediate peer is a configured trusted proxy.

    Holds the worker-level ``trusted_proxies`` (load balancers / reverse proxies
    in front of the worker) as a field, so it is built once per worker and reused
    across requests. ``trusted_proxies`` is NOT a per-circuit value, which is why
    resolution lives here rather than on :class:`ClientIPValidator`.
    """

    def __init__(self, trusted_proxies: Sequence[IPNetwork]) -> None:
        self._trusted_proxies = trusted_proxies

    def _is_trusted(self, ip: str) -> bool:
        if not self._trusted_proxies:
            return False
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return any(addr in net for net in self._trusted_proxies)

    def resolve(self, request: web.Request) -> str:
        """Resolve the effective client IP from an aiohttp request.

        The direct connection source is ``request.remote``; the forwarded chain
        is the raw ``X-Forwarded-For`` header, ordered original-client → ... →
        nearest proxy. Raises :class:`ClientIPNotAllowed` when the peer address
        cannot be determined.

        If the peer is not a trusted proxy, the header is ignored entirely and
        the peer address is returned, so a directly-exposed worker cannot be
        spoofed by a forged header. Otherwise the chain is walked from right
        (nearest) to left, skipping trusted-proxy hops, and the first untrusted
        address is returned as the real client. If every hop is a trusted proxy,
        the leftmost entry (the claimed original client) is used.
        """
        peer_ip = request.remote
        if not peer_ip:
            raise ClientIPNotAllowed("E20010: Unable to determine client address")
        forwarded_for = request.headers.get("X-Forwarded-For")
        if not forwarded_for or not self._is_trusted(peer_ip):
            return peer_ip
        chain = [part.strip() for part in forwarded_for.split(",") if part.strip()]
        for candidate in reversed(chain):
            if not self._is_trusted(candidate):
                return candidate
        return chain[0] if chain else peer_ip
