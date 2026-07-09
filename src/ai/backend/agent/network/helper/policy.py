"""Input policy for the privileged network helper (BEP-1058).

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
