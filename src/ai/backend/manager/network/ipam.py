"""Conflict-safe IPAM/VNI allocation for cluster-session networks.

Allocation state lives in etcd under ``network/ipam/*`` and is claimed with
``AsyncEtcd.put_if_absent`` (a compare-and-swap on ``create_revision == 0``),
replacing Swarm's internal global IPAM. See proposals/BEP-1055/control-plane.md.
"""

from __future__ import annotations

import ipaddress
import json
from typing import TYPE_CHECKING
from urllib.parse import quote

from ai.backend.manager.errors.network import NetworkPoolExhausted, VNIPoolExhausted

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd

DEFAULT_IPAM_POOL = "10.128.0.0/12"
DEFAULT_BLOCK_PREFIXLEN = 24
DEFAULT_VNI_RANGE = (4096, 16777215)

_ALLOCATED_PREFIX = "network/ipam/allocated"
_VNI_PREFIX = "network/ipam/vni"


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

    async def acquire(self, session_id: str) -> str:
        """Claim the first free block via CAS and return its CIDR.

        Raises:
            NetworkPoolExhausted: every block in the pool is already allocated.
        """
        pool = ipaddress.ip_network(self._pool)
        for candidate in pool.subnets(new_prefix=self._block_prefixlen):
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
