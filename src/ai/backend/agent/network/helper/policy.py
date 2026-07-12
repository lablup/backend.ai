"""Input policy for the privileged network helper (BEP-1062).

Pure, side-effect-free validation of everything the (untrusted) agent sends before
the helper acts on it. Two design rules keep this small and race-free:

- The agent sends only opaque identifiers and the manager's network parameters.
  It never sends device names, argv, netns paths, or CNI config, so there is no
  string/argv/config injection surface to filter — this module only bounds
  *identifiers* to a safe charset and *network parameters* to sane ranges.
- Namespace/PID safety is NOT done here (it is inherently I/O + TOCTOU-sensitive):
  it lives in the server, which opens the netns as a pinned fd and validates the fd
  itself. This module never touches ``/proc``.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from typing import Any

from ai.backend.common.network.types import NetworkBackendKind

# Opaque identifiers: a conservative charset so a value can never be mistaken for a
# CLI flag, a path component, or a shell/argv metacharacter downstream. session_id is
# a UUID-ish token; container_id is a containerd id (hex) or a kernel UUID.
_SESSION_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_CONTAINER_ID_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_MAC_RE = re.compile(r"\A[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}\Z")

# The helper only ever operates on RFC1918 space; a manager-provided subnet outside
# it is rejected outright (defence in depth — the bridge backend derives its own
# node-local subnet, but the overlay path trusts the manager's value).
_PRIVATE_POOLS = (
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
)

_VNI_MIN, _VNI_MAX = 1, (1 << 24) - 1  # VXLAN VNI is 24-bit
_MTU_MIN, _MTU_MAX = 576, 9000

# A published host port must be unprivileged: the helper runs as root, so a lying agent asking to
# publish on 22 or 443 would hijack the node's own SSH or TLS listener. Container ports are the
# far side of the DNAT and can be anything the image listens on.
_MIN_HOST_PORT = 1024
_MAX_PORT = 65535
# A kernel exposes a handful of services; a huge list would just be a way to flood the ruleset.
_MAX_PUBLISHED_PORTS = 64


class PolicyViolation(RuntimeError):
    """The agent sent an identifier or network parameter outside the allowed set.
    The message is intentionally generic — no privileged state leaks back."""


@dataclass(frozen=True)
class ValidatedNetworkConfig:
    backend: NetworkBackendKind
    subnet: str | None
    vni: int | None
    mtu: int


def validate_session_id(value: str) -> str:
    if not _SESSION_ID_RE.match(value):
        raise PolicyViolation("invalid session_id")
    return value


def validate_container_id(value: str) -> str:
    if not _CONTAINER_ID_RE.match(value):
        raise PolicyViolation("invalid container_id")
    return value


def validate_port_pairs(
    value: tuple[tuple[int, int], ...] | None,
) -> tuple[tuple[int, int], ...]:
    """Bound the agent-supplied (host_port, container_port) pairing.

    This is the trust boundary for host-port ingress. The destination address is never taken from
    the agent (the helper uses the LOCAL address it assigned at attach), so the only thing the
    agent can influence is *which* host port is redirected — hence the unprivileged-port floor and
    the duplicate check. The worst a lying agent achieves is publishing its own container on some
    other unprivileged port of the node.
    """
    if not value:
        raise PolicyViolation("missing ports")
    if len(value) > _MAX_PUBLISHED_PORTS:
        raise PolicyViolation("too many ports")
    seen: set[int] = set()
    for host_port, container_port in value:
        if not (_MIN_HOST_PORT <= host_port <= _MAX_PORT):
            raise PolicyViolation("host port out of range")
        if not (1 <= container_port <= _MAX_PORT):
            raise PolicyViolation("container port out of range")
        if host_port in seen:
            raise PolicyViolation("duplicate host port")
        seen.add(host_port)
    return value


def validate_ipv4(value: str | None, *, what: str) -> str:
    if value is None:
        raise PolicyViolation(f"missing {what}")
    try:
        ipaddress.IPv4Address(value)
    except ValueError as e:
        raise PolicyViolation(f"invalid {what}") from e
    return value


def validate_mac(value: str | None) -> str:
    if value is None or not _MAC_RE.match(value):
        raise PolicyViolation("invalid mac")
    return value


def validate_overlay_ip(value: str | None, subnet: str) -> str:
    """Validate an agent-supplied overlay endpoint IP: a real IPv4 confined to the session's
    own subnet (and not the network/broadcast address).

    This is the trust boundary for the manager-assigned static overlay address the agent
    relays. Confining it to the session subnet bounds the blast radius: the agent can only
    address its own session's isolated overlay (a separate VNI + subnet), never another
    session's fabric or the host — the worst a lying agent achieves is misconfiguring its own
    container's connectivity. The MAC is derived from this IP server-side (mac_for_ip), so the
    agent cannot forge a MAC independently of the (validated) IP."""
    validate_ipv4(value, what="overlay ip")
    addr = ipaddress.IPv4Address(value)
    try:
        net = ipaddress.ip_network(subnet, strict=False)
    except ValueError as e:
        raise PolicyViolation("invalid subnet") from e
    if (
        not isinstance(net, ipaddress.IPv4Network)
        or addr not in net
        or addr == net.network_address
        or addr == net.broadcast_address
    ):
        raise PolicyViolation("overlay ip outside session subnet")
    return str(value)


def _validate_subnet(subnet: str) -> str:
    try:
        net = ipaddress.ip_network(subnet, strict=False)
    except ValueError as e:
        raise PolicyViolation("invalid subnet") from e
    # Only IPv4 RFC1918 space is permitted; the pools are all IPv4 networks.
    if not isinstance(net, ipaddress.IPv4Network):
        raise PolicyViolation("subnet outside allowed private pools")
    for pool in _PRIVATE_POOLS:
        if net.subnet_of(pool):
            return subnet
    raise PolicyViolation("subnet outside allowed private pools")


def validate_network_config(raw: dict[str, Any]) -> ValidatedNetworkConfig:
    """Validate the manager-provided ``{backend, subnet, vni, mtu}``. Every field is
    treated as untrusted (it reaches the helper via the agent)."""
    try:
        backend = NetworkBackendKind(raw["backend"])
    except (KeyError, ValueError) as e:
        raise PolicyViolation("unknown network backend") from e

    subnet_raw = raw.get("subnet")
    subnet = _validate_subnet(str(subnet_raw)) if subnet_raw is not None else None

    vni_raw = raw.get("vni")
    vni: int | None = None
    if vni_raw is not None:
        try:
            vni = int(vni_raw)
        except (TypeError, ValueError) as e:
            raise PolicyViolation("invalid vni") from e
        if not (_VNI_MIN <= vni <= _VNI_MAX):
            raise PolicyViolation("vni out of range")

    mtu_raw = raw.get("mtu")
    mtu = _MTU_MIN
    if mtu_raw is not None:
        try:
            mtu = int(mtu_raw)
        except (TypeError, ValueError) as e:
            raise PolicyViolation("invalid mtu") from e
        if not (_MTU_MIN <= mtu <= _MTU_MAX):
            raise PolicyViolation("mtu out of range")

    return ValidatedNetworkConfig(backend=backend, subnet=subnet, vni=vni, mtu=mtu)
