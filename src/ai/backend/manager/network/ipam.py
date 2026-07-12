"""Conflict-safe IPAM/VNI allocation for cluster-session networks.

Allocation state lives in etcd under ``network/ipam/*`` and is claimed with
``AsyncEtcd.put_if_absent`` (a compare-and-swap on ``create_revision == 0``),
replacing Swarm's internal global IPAM. See proposals/BEP-1062/control-plane.md.
"""

from __future__ import annotations

import ipaddress
import json
from typing import TYPE_CHECKING
from urllib.parse import quote

from ai.backend.common.network.keys import endpoint_key, session_ipam_key
from ai.backend.common.network.types import mac_for_ip
from ai.backend.manager.errors.network import NetworkPoolExhausted, VNIPoolExhausted

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd

DEFAULT_IPAM_POOL = "10.128.0.0/12"
DEFAULT_BLOCK_PREFIXLEN = 24
DEFAULT_VNI_RANGE = (4096, 16777215)

_ALLOCATED_PREFIX = "network/ipam/allocated"
_VNI_PREFIX = "network/ipam/vni"


def _prefix_for_hosts(host_count: int, *, default_prefixlen: int, floor_prefixlen: int) -> int:
    """Smallest block (largest prefix) that holds ``host_count`` usable addresses.

    A fixed ``/24`` caps a session at 254 endpoints; a larger cluster needs a bigger
    block. Starts at ``default_prefixlen`` (``/24``) and widens (lowers the prefix) until
    the block is big enough, bounded by ``floor_prefixlen`` (the pool's own prefix).
    """
    prefixlen = default_prefixlen
    while prefixlen > floor_prefixlen and ((1 << (32 - prefixlen)) - 2) < max(host_count, 1):
        prefixlen -= 1
    return prefixlen


class SubnetAllocator:
    """Allocates per-session subnets from a pool using etcd CAS."""

    _etcd: AsyncEtcd
    _pool: str
    _block_prefixlen: int

    def __init__(
        self,
        etcd: AsyncEtcd,
        *,
        pool: str = DEFAULT_IPAM_POOL,
        block_prefixlen: int = DEFAULT_BLOCK_PREFIXLEN,
    ) -> None:
        self._etcd = etcd
        self._pool = pool
        self._block_prefixlen = block_prefixlen

    async def acquire(self, session_id: str, *, host_count: int = 1) -> str:
        """Claim the first free block sized for ``host_count`` endpoints, via CAS.

        The block prefix is chosen so the session subnet can hold every endpoint of the
        cluster (``host_count`` = total containers), removing the fixed-``/24`` 254-endpoint
        ceiling. ``host_count=1`` yields the default ``/24``.

        Raises:
            NetworkPoolExhausted: no free block of the required size remains.
        """
        pool = ipaddress.ip_network(self._pool)
        prefixlen = _prefix_for_hosts(
            host_count,
            default_prefixlen=self._block_prefixlen,
            floor_prefixlen=pool.prefixlen,
        )
        for candidate in pool.subnets(new_prefix=prefixlen):
            cidr = str(candidate)
            claimed = await self._etcd.put_if_absent(
                f"{_ALLOCATED_PREFIX}/{quote(cidr, safe='')}",
                json.dumps({"session_id": session_id}),
            )
            if claimed:
                return cidr
        raise NetworkPoolExhausted()

    async def release(self, subnet: str) -> None:
        await self._etcd.delete(f"{_ALLOCATED_PREFIX}/{quote(subnet, safe='')}")


class EndpointAllocator:
    """Assigns a per-endpoint overlay ``{ip, mac}`` centrally, via etcd CAS.

    Central assignment (vs per-node host-local IPAM) is what guarantees disjoint IPs
    across nodes on a stretched overlay subnet; the written ``endpoints/`` table is also
    the input the agent coordinator uses to program FDB/ARP proactively. See
    proposals/BEP-1062/control-plane.md.
    """

    _etcd: AsyncEtcd

    def __init__(self, etcd: AsyncEtcd) -> None:
        self._etcd = etcd

    async def assign(
        self, session_id: str, container_id: str, subnet: str, *, agent_id: str
    ) -> tuple[str, str]:
        """Claim the first free host IP in ``subnet`` for ``container_id`` (placed on
        ``agent_id``) and record the endpoint. Returns ``(ip, mac)``.

        ``agent_id`` is stored so a peer coordinator can resolve the endpoint's VTEP and
        skip its own local endpoints when programming FDB/ARP.

        Raises:
            NetworkPoolExhausted: the session subnet has no free host address.
        """
        for host in ipaddress.ip_network(subnet).hosts():
            ip = str(host)
            claimed = await self._etcd.put_if_absent(
                session_ipam_key(session_id, ip),
                json.dumps({"container_id": container_id}),
            )
            if not claimed:
                continue
            mac = mac_for_ip(ip)
            await self._etcd.put(
                endpoint_key(session_id, container_id),
                json.dumps({
                    "ip": ip,
                    "mac": mac,
                    "agent_id": agent_id,
                    "container_id": container_id,
                }),
            )
            return ip, mac
        raise NetworkPoolExhausted()

    async def release(self, session_id: str, container_id: str, ip: str) -> None:
        await self._etcd.delete(session_ipam_key(session_id, ip))
        await self._etcd.delete(endpoint_key(session_id, container_id))


class VNIAllocator:
    """Allocates VXLAN Network Identifiers; used only for the vxlan backend."""

    _etcd: AsyncEtcd
    _vni_range: tuple[int, int]

    def __init__(
        self,
        etcd: AsyncEtcd,
        *,
        vni_range: tuple[int, int] = DEFAULT_VNI_RANGE,
    ) -> None:
        self._etcd = etcd
        self._vni_range = vni_range

    async def acquire(self, session_id: str) -> int:
        """Claim the first free VNI via CAS.

        Raises:
            VNIPoolExhausted: every VNI in the range is already allocated.
        """
        low, high = self._vni_range
        for vni in range(low, high + 1):
            claimed = await self._etcd.put_if_absent(
                f"{_VNI_PREFIX}/{vni}",
                json.dumps({"session_id": session_id}),
            )
            if claimed:
                return vni
        raise VNIPoolExhausted()

    async def release(self, vni: int) -> None:
        await self._etcd.delete(f"{_VNI_PREFIX}/{vni}")
