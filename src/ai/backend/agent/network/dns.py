"""A container's ``resolv.conf`` for runtimes without dockerd's synthesized one.

Loopback nameservers are dropped: the host's stub is unreachable from the container's netns.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

HOST_RESOLV_CONF = Path("/etc/resolv.conf")
# systemd-resolved's "uplink" file: the real upstream nameservers behind the stub.
SYSTEMD_RESOLVED_UPLINK = Path("/run/systemd/resolve/resolv.conf")
# Last resort when the host exposes no non-loopback nameserver.
FALLBACK_NAMESERVERS = ("8.8.8.8", "8.8.4.4")


@dataclass
class ResolvConf:
    nameservers: list[str] = field(default_factory=list)
    search: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"nameserver {ns}" for ns in self.nameservers]
        if self.search:
            lines.append("search " + " ".join(self.search))
        if self.options:
            lines.append("options " + " ".join(self.options))
        return "\n".join(lines) + "\n"


def _is_loopback(address: str) -> bool:
    # A nameserver may carry a zone/scope suffix (fe80::1%eth0); ipaddress rejects it.
    try:
        return ipaddress.ip_address(address.split("%", 1)[0]).is_loopback
    except ValueError:
        # Not an IP literal: keep it.
        return False


def parse_resolv_conf(text: str) -> ResolvConf:
    """Parse the nameserver/search/options directives of a resolv.conf."""
    parsed = ResolvConf()
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].split(";", 1)[0].strip()
        if not line:
            continue
        keyword, _, rest = line.partition(" ")
        match keyword:
            case "nameserver":
                if value := rest.strip():
                    parsed.nameservers.append(value)
            case "search":
                parsed.search.extend(rest.split())
            case "options":
                parsed.options.extend(rest.split())
    return parsed


def _read(path: Path) -> ResolvConf | None:
    try:
        return parse_resolv_conf(path.read_text())
    except OSError:
        return None


def resolve_container_dns(
    configured_nameservers: Sequence[str] = (),
    *,
    host_resolv_conf: Path = HOST_RESOLV_CONF,
    systemd_uplink: Path = SYSTEMD_RESOLVED_UPLINK,
) -> ResolvConf:
    """A container's resolv.conf: configured > host's non-loopback > systemd uplink > fallback.

    ``search``/``options`` come from the host; ``ndots`` is forced to 0 (bare cluster names first).
    """
    host = _read(host_resolv_conf)
    inherited_options = list(host.options) if host else []
    result = ResolvConf(
        search=list(host.search) if host else [],
        options=[o for o in inherited_options if not o.startswith("ndots:")] + ["ndots:0"],
    )

    if configured_nameservers:
        result.nameservers = list(configured_nameservers)
        return result

    if host is not None:
        if usable := [ns for ns in host.nameservers if not _is_loopback(ns)]:
            result.nameservers = usable
            return result

    # The host's own resolver is loopback-only (or unreadable): reach past the stub.
    if (uplink := _read(systemd_uplink)) is not None:
        if usable := [ns for ns in uplink.nameservers if not _is_loopback(ns)]:
            result.nameservers = usable
            return result

    result.nameservers = list(FALLBACK_NAMESERVERS)
    return result
