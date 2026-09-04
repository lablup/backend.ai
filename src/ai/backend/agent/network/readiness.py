"""Whether this node can actually serve a vxlan overlay session, checked before one arrives.

The agent advertised ``backends: ["vxlan"]`` unconditionally, so a host missing ``xt_u32``, or one
whose CNI already owns UDP/4789, was scheduled a session it could only fail -- at create time, on
one node, as a session that never reaches RUNNING. Everything here is read-only and cheap enough
to run at startup; what it finds is published beside the capabilities so an operator sees it where
they are already looking.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

#: Devices this backend made. Anything else on our port or in our VNI range belongs to someone
#: else, and the plaintext-drop and mark rules match on (port, VNI) alone -- so an overlap means
#: this node's rules act on a stranger's traffic, and theirs on ours.
OURS_PREFIX: Final = "baivx"

_REQUIRED_BINARIES: Final = ("ip", "bridge", "iptables")
#: The two iptables matches the encrypted path needs: `u32` picks the VNI out of the encapsulation
#: and `policy` tells an ESP-decapsulated frame from an injected one.
_REQUIRED_MATCHES: Final = ("u32", "policy")

_HEADER = re.compile(r"^\d+:\s+(?P<name>[^:@\s]+)[@:]")


@dataclass(frozen=True)
class VxlanDevice:
    """One vxlan device on this host, as `ip -d link` describes it."""

    name: str
    vni: int
    dstport: int

    @property
    def is_ours(self) -> bool:
        return self.name.startswith(OURS_PREFIX)


def parse_vxlan_details(raw: str) -> tuple[VxlanDevice, ...]:
    """Devices from ``ip -d link show type vxlan``.

    The multi-line form on purpose: ``-o`` truncates the very attribute line this needs (measured
    on 6.14 -- the one-line output ends at ``vxlan id <n>`` and never reaches ``dstport``), and
    ``-j`` is malformed or empty depending on the kernel. The ``vxlan id`` line also carries a
    bare ``fan-map`` token between the id and the rest on some kernels, which is why this reads
    keywords by position rather than splitting on a fixed layout.
    """
    devices: list[VxlanDevice] = []
    name: str | None = None
    for line in raw.splitlines():
        if (match := _HEADER.match(line)) is not None:
            name = match.group("name")
            continue
        stripped = line.strip()
        if name is None or not stripped.startswith("vxlan id "):
            continue
        tokens = stripped.split()
        vni = _int_after(tokens, "id")
        dstport = _int_after(tokens, "dstport")
        if vni is not None and dstport is not None:
            devices.append(VxlanDevice(name=name, vni=vni, dstport=dstport))
        name = None
    return tuple(devices)


def _int_after(tokens: Sequence[str], key: str) -> int | None:
    for index, token in enumerate(tokens):
        if token == key and index + 1 < len(tokens):
            try:
                return int(tokens[index + 1])
            except ValueError:
                return None
    return None


def foreign_conflicts(
    devices: Sequence[VxlanDevice],
    *,
    port: int,
    vni_range: tuple[int, int],
) -> list[str]:
    """What another VXLAN on this host would break, in the operator's words.

    Two distinct collisions, and the port one is the dangerous half: the drop and mark rules
    select on (UDP port, VNI) and nothing else, so a co-tenant on our port with a VNI in our range
    has its frames marked for our XFRM policy, or dropped as unprotected plaintext.
    """
    low, high = vni_range
    problems: list[str] = []
    for device in devices:
        if device.is_ours:
            continue
        if device.dstport == port and low <= device.vni <= high:
            problems.append(
                f"{device.name} carries VNI {device.vni} on udp/{device.dstport}, inside this "
                f"cluster's VNI range {low}-{high} on its own port: a session drawing that VNI "
                f"would have its rules act on {device.name}'s traffic and vice versa. Move one of "
                "the two off the shared port (the manager's `vxlan-port`) or out of the range."
            )
        elif device.dstport == port:
            problems.append(
                f"{device.name} shares udp/{device.dstport} with this cluster's overlay. Its VNI "
                f"({device.vni}) is outside the allocation range {low}-{high} today, so nothing "
                "collides yet; a range change would make it."
            )
    return problems


async def _binary_present(name: str) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            name,
            "-V",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except OSError:
        return False
    await proc.communicate()
    return True


async def _match_present(name: str) -> bool:
    """Whether iptables can load a match. Needs no privilege and mutates nothing."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "iptables",
            "-m",
            name,
            "--help",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except OSError:
        return False
    await proc.communicate()
    return proc.returncode == 0


async def _vxlan_details() -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ip",
            "-d",
            "link",
            "show",
            "type",
            "vxlan",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
    except OSError:
        return ""
    return stdout.decode(errors="replace") if proc.returncode == 0 else ""


async def probe_readiness(*, port: int, vni_range: tuple[int, int]) -> list[str]:
    """Everything that would stop this node from serving an overlay session, or an empty list.

    Read-only. It reports rather than refuses: a node that cannot encrypt still refuses the
    session when one arrives (that guard is in the backend and must stay there), and refusing to
    start the agent over a missing match would take its single-node sessions down with it.
    """
    problems: list[str] = []
    for binary in _REQUIRED_BINARIES:
        if not await _binary_present(binary):
            problems.append(
                f"`{binary}` is not on this node's PATH; the overlay is built by shelling out to "
                "it, so a session scheduled here cannot be set up."
            )
    for match in _REQUIRED_MATCHES:
        if not await _match_present(match):
            problems.append(
                f"iptables has no `{match}` match (xt_{match}). An encrypted session needs it to "
                "tell its own VNI's frames apart, and is refused on this node without it."
            )
    problems.extend(
        foreign_conflicts(
            parse_vxlan_details(await _vxlan_details()), port=port, vni_range=vni_range
        )
    )
    return problems
