"""The node's VXLAN tunnel endpoint: which address it is, and whether it can carry a tunnel.

Shared by the agent and the privileged network helper, because whichever of the two owns the host's
networking is the one that publishes this node's `Member.vtep_ip` — the address every peer programs
into its FDB. Peers guard on ``vtep_ip is None`` and nothing else, so an unusable address published
here does not fail: it builds an overlay that comes up, logs nothing, and carries no traffic.
"""

from __future__ import annotations

import ipaddress
import socket

import psutil


def live_iface_for_ip(host_ip: str) -> str | None:
    """The UP interface that holds ``host_ip``, or None if this host cannot send from it.

    Holding the address is not enough: psutil reports the addresses of DOWN interfaces too, and a
    vxlan device created on a down uplink comes up happily and carries nothing.
    """
    stats = psutil.net_if_stats()
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == host_ip:
                if iface in stats and stats[iface].isup:
                    return iface
    return None


def uplink_for_ip(host_ip: str) -> str:
    """The interface to build the vxlan device on: the one carrying this node's VTEP, so the
    overlay rides the same L2 the agents reach each other on. Falls back to ``eth0`` when no live
    interface holds the address (single-node / misconfiguration)."""
    return live_iface_for_ip(host_ip) or "eth0"


def usable_vtep(host_ip: str) -> str | None:
    """``host_ip`` if it can actually anchor a vxlan tunnel, else None.

    The VTEP comes from ``container.advertised-host`` (or ``bind-host``), whose defaults are the
    unusable ``""`` and ``0.0.0.0``: a peer that seeds ``""`` into ``bridge fdb append ... dst ''``
    fails outright, and ``0.0.0.0`` is accepted but points nowhere. So it must be a concrete unicast
    IPv4, routable off-link, held by an interface of this host that is up.

    Rejected, and why: ``""`` and an FQDN (neither is something iproute2 can take as an FDB
    destination); IPv6 (the vxlan path is IPv4-only end to end — see `uplink_for_ip` and
    `vxlan_link_add_args`); ``0.0.0.0``; loopback; multicast/reserved; and link-local (169.254/16,
    what a host holds when DHCP failed — real, held, and unreachable from another subnet).

    None means this node cannot join a multi-node overlay session. Single-node sessions never touch
    the VTEP, which is why this is not fatal on its own.
    """
    try:
        addr = ipaddress.IPv4Address(host_ip)
    except ipaddress.AddressValueError:
        return None
    if (
        addr.is_unspecified
        or addr.is_loopback
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_link_local
    ):
        return None
    return host_ip if live_iface_for_ip(host_ip) is not None else None
