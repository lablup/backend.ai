"""Whether this node can actually serve a vxlan overlay session, checked before one arrives.

The agent advertised ``backends: ["vxlan"]`` unconditionally, so a host missing ``xt_u32``, or one
whose CNI already owns UDP/4789, was scheduled a session it could only fail -- at create time, on
one node, as a session that never reaches RUNNING. Everything here is read-only and cheap enough
to run at startup; what it finds is published beside the capabilities so an operator sees it where
they are already looking.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from ai.backend.agent.errors.network import UndescribableVxlanDevice
from ai.backend.logging import BraceStyleAdapter

#: Devices this backend made. Anything else on our port or in our VNI range belongs to someone
#: else, and the plaintext-drop and mark rules match on (port, VNI) alone -- so an overlap means
#: this node's rules act on a stranger's traffic, and theirs on ours.
OURS_PREFIX: Final = "baivx"

_REQUIRED_BINARIES: Final = ("ip", "bridge", "iptables")
#: The two iptables matches the encrypted path needs: `u32` picks the VNI out of the encapsulation
#: and `policy` tells an ESP-decapsulated frame from an injected one.
_REQUIRED_MATCHES: Final = ("u32", "policy")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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


async def _run(argv: Sequence[str]) -> str | None:
    """The command's stdout, or None when it did not complete successfully."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
    except OSError:
        return None
    return stdout.decode(errors="replace") if proc.returncode == 0 else None


async def _vxlan_names() -> tuple[str, ...]:
    """Every vxlan device's name, from the one `ip link` form that is reliable here.

    ``ip -o link show type vxlan`` (no ``-d``) is the same on every kernel this has been run on;
    the detailed variants are not -- see `describe_vxlan_devices`.
    """
    raw = await _run(["ip", "-o", "link", "show", "type", "vxlan"])
    if raw is None:
        return ()
    names: list[str] = []
    for line in raw.splitlines():
        if (match := _HEADER.match(line)) is not None:
            names.append(match.group("name"))
    return tuple(names)


async def describe_vxlan_devices() -> tuple[tuple[VxlanDevice, ...], tuple[str, ...]]:
    """Every vxlan device this host can describe, and the names of the ones it cannot.

    ``ip -d`` is not dependable here and the failure is not a clean error. On three hosts running
    the same iproute2 6.1.0 it SEGFAULTS, in opposite directions: one crashes on
    ``ip -d link show type vxlan`` and answers ``ip -d link show dev <name>``, another does the
    reverse, a third answers both. (The JSON variants are separately malformed or empty by
    kernel version -- see `_list_vxlan_devices` in the vxlan backend.) So both forms are tried,
    and what neither could describe is RETURNED rather than dropped: reporting "no conflict"
    because the host could not be asked is the fail-open this check exists to remove.
    """
    listing = await _run(["ip", "-d", "link", "show", "type", "vxlan"])
    if listing is not None:
        return parse_vxlan_details(listing), ()
    described: list[VxlanDevice] = []
    unreadable: list[str] = []
    for name in await _vxlan_names():
        per_device = await _run(["ip", "-d", "link", "show", "dev", name])
        parsed = parse_vxlan_details(per_device) if per_device is not None else ()
        if parsed:
            described.extend(parsed)
        else:
            unreadable.append(name)
    return tuple(described), tuple(unreadable)


@dataclass(frozen=True)
class Readiness:
    """What this node found out about its own ability to serve an overlay session.

    Two kinds, because they call for different answers. ``blocking`` is settled and local -- a
    missing binary or iptables match makes every session here fail the same way, so the node
    should stop advertising the backend rather than accept work it cannot do. ``advisory``
    depends on which VNI a session happens to draw, so it is reported and left to the operator;
    the exact collision is refused at setup, where the session's real port and VNI are known.
    """

    blocking: tuple[str, ...] = ()
    advisory: tuple[str, ...] = ()

    @property
    def problems(self) -> list[str]:
        return [*self.blocking, *self.advisory]

    @property
    def can_serve_overlay(self) -> bool:
        return not self.blocking


async def probe_readiness(
    *,
    port: int,
    vni_range: tuple[int, int],
    privnet_socket: str | None = None,
    recovery_problems: Mapping[str, str] | None = None,
) -> Readiness:
    """Everything that would stop this node from serving an overlay session.

    Read-only, and run at startup: the point is that the reason exists BEFORE a session is
    scheduled here and fails on one node with it buried in a create-time traceback.
    """
    blocking: list[str] = []
    for binary in _REQUIRED_BINARIES:
        if not await _binary_present(binary):
            blocking.append(
                f"`{binary}` is not on this node's PATH; the overlay is built by shelling out to "
                "it, so a session scheduled here cannot be set up."
            )
    for match in _REQUIRED_MATCHES:
        if not await _match_present(match):
            blocking.append(
                f"iptables has no `{match}` match (xt_{match}). An encrypted session needs it to "
                "tell its own VNI's frames apart, and is refused on this node without it."
            )
    for backend_name, problem in (recovery_problems or {}).items():
        # A node that could not close what it left behind holds devices whose protection it cannot
        # vouch for. Blocking, not advisory: a new session would be built beside them.
        blocking.append(
            f"the {backend_name} backend could not bring down the tunnels that survived a previous"
            f" life on this node ({problem}); until they are down, what they carry is unknown"
        )
    if privnet_socket is not None:
        # On a privnet-backed node every device, rule and XFRM object is made by that process.
        # Checking only the local binaries said this node was ready while the thing that would
        # actually do the work was not running -- and the session found out one node at a time,
        # at create time, from a bare connection error.
        from ai.backend.agent.network.privnet.client import PrivNetClient

        if (unreachable := await PrivNetClient(privnet_socket).reachable()) is not None:
            blocking.append(unreachable)
    devices, unreadable = await describe_vxlan_devices()
    advisory = foreign_conflicts(devices, port=port, vni_range=vni_range)
    if unreadable:
        advisory.append(
            f"this host's `ip -d link` cannot describe {', '.join(unreadable)} (it exits non-zero"
            " or crashes on both of its forms), so a VXLAN already using this cluster's port or"
            " VNI range cannot be ruled out here. Check by hand before co-hosting another"
            " overlay."
        )
    return Readiness(blocking=tuple(blocking), advisory=tuple(advisory))


async def conflicting_device(*, port: int, vni: int) -> str | None:
    """The name of a foreign VXLAN already using this exact (port, VNI), if there is one.

    Checked at setup rather than at startup because that is where the port and VNI are finally
    known -- the manager configures the port and allocates the VNI, and neither reaches the agent
    until a session does. An overlap here is not advisory: the drop and mark rules select on
    (port, VNI) alone, so the two tunnels would act on each other's traffic.
    """
    devices, unreadable = await describe_vxlan_devices()
    for device in devices:
        if not device.is_ours and device.dstport == port and device.vni == vni:
            return device.name
    # Only OUR devices being undescribable is not a hazard: we know their VNI from their name,
    # and two of our own sessions never share one. A FOREIGN device we could not read is the
    # dangerous case -- it may be on this exact port and VNI, and the drop and mark rules select
    # on nothing else -- and "could not check" must not be reported as "no conflict".
    foreign_unreadable = [name for name in unreadable if not name.startswith(OURS_PREFIX)]
    if foreign_unreadable:
        raise UndescribableVxlanDevice(
            f"refusing VNI {vni} on udp/{port}: this host has VXLAN device(s)"
            f" ({', '.join(foreign_unreadable)}) that `ip -d link` cannot describe -- it exits"
            " non-zero or crashes on both of its forms -- so a collision with them cannot be"
            " ruled out, and a collision means each side's firewall rules act on the other's"
            " traffic. Give this cluster its own UDP port (the manager's `vxlan-port`), or"
            " remove the device."
        )
    return None
