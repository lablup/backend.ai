"""Container DNS resolution for the containerd backend (BEP-1062).

The Docker backend gets this for free: dockerd synthesizes a per-container ``resolv.conf`` and
bind-mounts it over ``/etc/resolv.conf``. Building the OCI spec ourselves means nobody does it,
so a containerd kernel would start with whatever ``/etc/resolv.conf`` the image happens to ship
(usually none) and resolve no names at all.

Nothing here needs privilege: we write a file into the kernel's own scratch and bind-mount it,
exactly as ``_prepare_etc_hosts`` does. The host's resolver files are only ever read.

The one subtlety is *which* nameservers to use. A container lives in its own network namespace,
so a loopback nameserver on the host — most commonly the systemd-resolved stub at 127.0.0.53 —
is unreachable from inside it: the container's 127.0.0.1 is its own, and nothing listens there.
Copying the host's ``/etc/resolv.conf`` verbatim is therefore the one thing that looks right and
silently does not work. We drop loopback nameservers and fall back to the systemd-resolved uplink
file, which holds the real upstream servers.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

# The resolver the host's /etc/resolv.conf points at. On a systemd-resolved system this is the
# 127.0.0.53 stub, which is useless inside a container's network namespace.
HOST_RESOLV_CONF = Path("/etc/resolv.conf")
# systemd-resolved's "uplink" file: the real upstream nameservers behind the stub.
SYSTEMD_RESOLVED_UPLINK = Path("/run/systemd/resolve/resolv.conf")
# Last resort when the host exposes no usable nameserver (e.g. an all-loopback resolv.conf and no
# systemd-resolved). Without this the container would have no resolver at all.
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
        # Not an IP literal at all — leave it alone rather than silently dropping it.
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
    """Decide what a container's /etc/resolv.conf should contain.

    Precedence: operator-configured nameservers > the host's own (loopback dropped) > the
    systemd-resolved uplink > a public fallback.

    ``search``/``options`` are carried over from the host's resolv.conf whenever we have one, so
    short-name lookups keep working; they are harmless even when the nameservers came from
    elsewhere.
    """
    host = _read(host_resolv_conf)
    result = ResolvConf(
        search=list(host.search) if host else [],
        options=list(host.options) if host else [],
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
