"""Client-IP allowlist matching for the per-circuit ``allowed_client_ips``
restriction, shared by the coordinator (Traefik config generation) and the
worker (Python-mode enforcement).

The allowlist is persisted on a circuit as a comma-separated string of CIDR
blocks or bare IP addresses (``Circuit.allowed_client_ips``). A null/blank value
means the circuit is reachable from anywhere.

Resolving the real client IP from ``X-Forwarded-For`` is handled separately: the
worker installs ``aiohttp_remotes.XForwardedStrict`` as a middleware (see
:class:`ai.backend.appproxy.worker.proxy.frontend.http.base.BaseHTTPFrontend`),
so ``request.remote`` already holds the real client IP — trusted only when the
connection arrives through the configured ``trusted_proxies`` — by the time this
validator runs.
"""

import ipaddress
import logging

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
