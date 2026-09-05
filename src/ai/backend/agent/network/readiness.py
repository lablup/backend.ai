"""Whether this node can actually serve a vxlan overlay session, checked before one arrives.

The agent advertised ``backends: ["vxlan"]`` unconditionally, so a host missing ``xt_u32``, or one
whose CNI already owns UDP/4789, was scheduled a session it could only fail -- at create time, on
one node, as a session that never reaches RUNNING. Everything here is read-only and cheap enough
to run at startup; what it finds is published beside the capabilities so an operator sees it where
they are already looking.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ai.backend.agent.errors.network import UndescribableVxlanDevice
from ai.backend.agent.network import command
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


#: Present exactly when the kernel has the XFRM framework compiled in. Reading it needs no
#: privilege, which matters: on a privnet-backed node this probe runs in the AGENT, which holds no
#: CAP_NET_ADMIN and so cannot ask netlink the same question.
#: The AEAD every overlay SA is built with; the backend programs this exact string.
_ESP_AEAD = "rfc4106(gcm(aes))"
_XFRM_STAT = Path("/proc/net/xfrm_stat")
#: Every algorithm the kernel's crypto API can instantiate, one `name : <value>` line each.
_PROC_CRYPTO = Path("/proc/crypto")


def _encryption_problems() -> list[str]:
    """What would stop this node holding up its end of an ESP tunnel.

    Static, not functional: it reads what the kernel says it has rather than installing an SA and
    watching a packet. A real self-test would need CAP_NET_ADMIN and a namespace to do it in, and
    on a privnet-backed node this code runs in the agent, which has neither. What it does catch is
    the two ways a node genuinely cannot do this -- no XFRM in the kernel, no AES-GCM in its
    crypto API -- which is what a node advertising the profile would otherwise have claimed.
    """
    problems: list[str] = []
    if not _XFRM_STAT.exists():
        problems.append(
            "this kernel has no XFRM framework (/proc/net/xfrm_stat is absent), so it cannot"
            " install the ESP state an encrypted overlay is built from."
        )
    try:
        crypto = _PROC_CRYPTO.read_text()
    except OSError:
        problems.append(
            "this node's /proc/crypto cannot be read, so whether the kernel offers"
            f" {_ESP_AEAD} for the overlay's ESP cannot be established."
        )
    else:
        if _ESP_AEAD not in crypto:
            problems.append(
                f"this kernel's crypto API does not offer {_ESP_AEAD}, which is the AEAD every"
                " overlay SA is built with."
            )
    return problems


async def _binary_present(name: str) -> bool:
    try:
        await command.run([name, "-V"], capture_stderr=False)
    except (OSError, command.CommandTimeout):
        # A binary that will not answer is one this node cannot rely on, and a probe that hangs
        # stops the agent's startup: every one of these runs before the node is ready to serve.
        return False
    return True


async def _match_present(name: str) -> bool:
    """Whether iptables can load a match. Needs no privilege and mutates nothing."""
    try:
        rc, _, _ = await command.run(["iptables", "-m", name, "--help"], capture_stderr=False)
    except (OSError, command.CommandTimeout):
        return False
    return rc == 0


async def _run(argv: Sequence[str]) -> str | None:
    """The command's stdout, or None when it did not complete successfully.

    A command that hangs answers None like any other failure. These run while the agent is
    deciding whether it may serve at all, so waiting forever is not the cautious option -- it is a
    node that never finishes starting and never says why.
    """
    try:
        rc, stdout, _ = await command.run(argv, capture_stderr=False)
    except (OSError, command.CommandTimeout):
        return None
    return stdout.decode(errors="replace") if rc == 0 else None


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
    #: What would stop this node from ENCRYPTING one. A superset of `blocking` in effect -- a node
    #: that cannot carry an overlay cannot carry an encrypted one -- but reported apart, because a
    #: cluster may legitimately run unencrypted on a kernel with no ESP.
    encryption_blocking: tuple[str, ...] = ()

    @property
    def problems(self) -> list[str]:
        return [*self.blocking, *self.advisory, *self.encryption_blocking]

    @property
    def can_serve_overlay(self) -> bool:
        return not self.blocking

    @property
    def can_encrypt_overlay(self) -> bool:
        return not self.blocking and not self.encryption_blocking


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
    encryption_blocking = _encryption_problems()
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
    from ai.backend.agent.network.pair_journal import PairJournal
    from ai.backend.agent.network.vni_registry import VniRegistry

    if (journal_problem := PairJournal().unusable_reason()) is not None:
        blocking.append(journal_problem)
    if (registry_problem := VniRegistry().unusable_reason()) is not None:
        # Without it this node cannot tell whether a declared VNI is already another session's,
        # and setup deletes the devices of whatever holds it.
        blocking.append(registry_problem)
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

        client = PrivNetClient(privnet_socket)
        if (unreachable := await client.reachable()) is not None:
            blocking.append(unreachable)
        else:
            for what, why in sorted((await client.recovery_problems()).items()):
                # Blocking. A node whose privnet cannot take charge of something already running
                # on it looks healthy from every other angle, and the manager goes on scheduling
                # onto it -- while that session's VNI can be handed out underneath it.
                blocking.append(f"the privileged network helper has not recovered {what}: {why}")
    devices, unreadable = await describe_vxlan_devices()
    advisory = foreign_conflicts(devices, port=port, vni_range=vni_range)
    if unreadable:
        advisory.append(
            f"this host's `ip -d link` cannot describe {', '.join(unreadable)} (it exits non-zero"
            " or crashes on both of its forms), so a VXLAN already using this cluster's port or"
            " VNI range cannot be ruled out here. Check by hand before co-hosting another"
            " overlay."
        )
    return Readiness(
        blocking=tuple(blocking),
        advisory=tuple(advisory),
        encryption_blocking=tuple(encryption_blocking),
    )


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
