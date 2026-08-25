"""What this node's underlay can actually carry, measured rather than assumed.

The manager computes a session's overlay MTU as a *configured* underlay constant minus the tunnel
overhead (see manager/network/cni.py); nothing consults the real path. That holds only while the
pod network does no encapsulation of its own. Measured on a two-node cluster, with the manager left
at its 1500 default (so the overlay is 1450) and the largest DF payload that actually crossed:

    flannel host-gw     underlay 1500 -> 1422 == what 1450 promises   ok
    flannel vxlan       underlay 1450 -> 1372, 50 bytes short
    flannel ipip        underlay 1480 -> 1402, 20 bytes short
    flannel wireguard   underlay 1420 -> 1342, 80 bytes short
    calico vxlan/ipip   underlay 1450/1480 -> 1372/1402
    cilium vxlan        underlay 1450 -> 1372, 50 bytes short
    cilium native       underlay 1500 -> 1422                          ok

The shortfall is invisible: small packets pass, full-size frames vanish with no ICMP, and the
failure surfaces much later as a hang in bulk transfer. So the number is worth measuring.

**Reading the device MTU alone is not enough.** cilium in tunnel mode leaves the pod's ``eth0`` at
1500 and puts ``mtu 1450`` on the pod's *default route* instead (measured), so a device-only
reading is exactly the 50 bytes too optimistic that black-hole traffic. flannel and calico do the
opposite -- they lower the device MTU and leave the route alone -- so a route-only reading misses
those. Both are consulted and the smaller wins.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from pathlib import Path

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

CommandReader = Callable[[list[str]], Awaitable[str]]
DevMtuReader = Callable[[str], Awaitable[int | None]]

_MTU_RE = re.compile(r"\bmtu\s+(\d+)\b")


def parse_route_mtus(output: str) -> list[int]:
    """Every ``mtu N`` an ``ip route`` listing carries.

    A route without an ``mtu`` attribute imposes no constraint of its own (the device MTU applies),
    so it contributes nothing here rather than a default -- otherwise the common case would look
    like a 1500-byte ceiling on a device that is smaller.
    """
    return [int(m) for m in _MTU_RE.findall(output)]


async def _read_command(argv: list[str]) -> str:
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    out, _ = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(argv)} exited {proc.returncode}")
    return out.decode(errors="replace")


async def _read_dev_mtu(dev: str) -> int | None:
    try:
        return int(Path(f"/sys/class/net/{dev}/mtu").read_text().strip())
    except (OSError, ValueError):
        return None


async def underlay_mtu(
    uplink: str,
    *,
    peer_ip: str | None = None,
    read_command: CommandReader = _read_command,
    read_dev_mtu: DevMtuReader = _read_dev_mtu,
) -> int | None:
    """The largest outer packet this node can send over ``uplink``, or None if it cannot be told.

    ``peer_ip``, when given, is queried with ``ip route get`` so a per-destination MTU is picked up
    for the destination that actually matters; without it the node's default route is used, which
    is where cilium puts its tunnel MTU.

    None (rather than a guess) when nothing could be read: an unmeasurable path must not be
    reported as a small one, or every session on a node with an odd setup would be refused.
    """
    candidates: list[int] = []
    dev_mtu = await read_dev_mtu(uplink)
    if dev_mtu:
        candidates.append(dev_mtu)
    argv = (
        ["ip", "-4", "route", "get", peer_ip]
        if peer_ip
        else ["ip", "-4", "route", "show", "default", "dev", uplink]
    )
    try:
        candidates.extend(parse_route_mtus(await read_command(argv)))
    except (RuntimeError, OSError, FileNotFoundError) as e:
        log.debug("could not read route MTU via {}: {!r}", " ".join(argv), e)
    return min(candidates) if candidates else None
