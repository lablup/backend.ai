"""Does this session's tunnel actually carry anything?

Everything else about a VXLAN overlay reports success while carrying nothing: the devices come
up, the FDB and ARP entries are programmed, no command fails. Measured, a Calico cluster does
exactly that to us -- Felix drops workload-originated UDP on its ``vxlanPort`` (4789 by default,
the same port we ship) on the host side of every pod veth, in *every* encapsulation mode. The
session then hangs at rendezvous with nothing in any log.

Two things rule out just looking for the offending rule. It lives in the **node's** netns while a
containerised (fatPod) agent runs in the **pod's** -- measured, the two filter tables share
nothing -- so the agent cannot see it. And a rule scan only ever finds the filters we thought to
look for. Sending a frame and waiting for the answer tests the path itself.

ARP, because the overlay bridge has no IP address (``isGateway: False``) and so cannot source an
IP probe, while ARP needs none: a request may carry sender 0.0.0.0, and a Linux peer answers a
request for its own address regardless (this is how duplicate-address detection works). The
request is sent **unicast to the endpoint's known MAC**, so a reply proves the whole chain the
session depends on -- our FDB entry for that MAC, the tunnel, the peer's bridge, the container,
and the return path -- rather than just that broadcast flooding works.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
import struct
from pathlib import Path
from typing import Final

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_ETH_P_ARP: Final = 0x0806
_ARP_REQUEST: Final = 1
_ARP_REPLY: Final = 2
_ETH_HDR_LEN: Final = 14
_ARP_LEN: Final = 28
# A frame big enough for any ARP reply; nothing larger is of interest here.
_RECV_BUF: Final = 256


def _mac_bytes(mac: str) -> bytes:
    return bytes.fromhex(mac.replace(":", ""))


def build_arp_request(src_mac: str, target_mac: str, target_ip: str) -> bytes:
    """A unicast ARP request for ``target_ip``, addressed to ``target_mac``.

    Sender protocol address is 0.0.0.0: the probe claims no address on the overlay (the bridge has
    none), and a request that claimed one could collide with a container's.
    """
    dst = _mac_bytes(target_mac)
    src = _mac_bytes(src_mac)
    ether = dst + src + struct.pack("!H", _ETH_P_ARP)
    arp = struct.pack(
        "!HHBBH6s4s6s4s",
        1,  # htype: Ethernet
        0x0800,  # ptype: IPv4
        6,
        4,
        _ARP_REQUEST,
        src,
        ipaddress.IPv4Address("0.0.0.0").packed,
        dst,
        ipaddress.IPv4Address(target_ip).packed,
    )
    return ether + arp


def is_arp_reply_from(frame: bytes, target_ip: str) -> bool:
    """Whether ``frame`` is an ARP reply announcing ``target_ip``.

    Matching on the sender protocol address alone: the reply's destination is our MAC, which the
    socket already filtered by binding to the bridge, and a gratuitous ARP from the same endpoint
    is just as good an answer to "does the tunnel carry traffic".
    """
    if len(frame) < _ETH_HDR_LEN + _ARP_LEN:
        return False
    if struct.unpack("!H", frame[12:14])[0] != _ETH_P_ARP:
        return False
    arp = frame[_ETH_HDR_LEN : _ETH_HDR_LEN + _ARP_LEN]
    oper = struct.unpack("!H", arp[6:8])[0]
    if oper != _ARP_REPLY:
        return False
    return arp[14:18] == ipaddress.IPv4Address(target_ip).packed


def read_mac(dev: str) -> str | None:
    try:
        return Path(f"/sys/class/net/{dev}/address").read_text().strip()
    except OSError:
        return None


async def arp_probe(
    bridge: str, target_ip: str, target_mac: str, *, reply_wait_sec: float = 2.0
) -> bool | None:
    """True if ``target_ip`` answered over ``bridge``, False if it did not, None if unprobeable.

    None (not False) when the probe itself could not run -- no such device, no CAP_NET_RAW, a
    kernel without AF_PACKET. A diagnostic must never be mistaken for a diagnosis.

    ``reply_wait_sec`` is how long to listen, not a cancellation deadline, which is why it lives
    here rather than in an ``asyncio.timeout`` around the call: "nobody answered" is this
    function's *result*, and a timeout raised at the call site could not express it.
    """
    src_mac = read_mac(bridge)
    if src_mac is None:
        return None
    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(_ETH_P_ARP))
    except (OSError, AttributeError) as e:
        log.debug("overlay probe unavailable: {!r}", e)
        return None
    try:
        sock.bind((bridge, 0))
        sock.setblocking(False)
        loop = asyncio.get_running_loop()
        await loop.sock_sendall(sock, build_arp_request(src_mac, target_mac, target_ip))
        deadline = loop.time() + reply_wait_sec
        while (remaining := deadline - loop.time()) > 0:
            try:
                frame = await asyncio.wait_for(loop.sock_recv(sock, _RECV_BUF), remaining)
            except TimeoutError:
                break
            else:
                # Frames other than the answer land here too (our own request, unrelated ARP), so
                # keep listening until the deadline rather than taking the first one as a verdict.
                if is_arp_reply_from(frame, target_ip):
                    return True
        return False
    except OSError as e:
        log.debug("overlay probe failed to run on {}: {!r}", bridge, e)
        return None
    finally:
        sock.close()
