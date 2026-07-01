"""Conflict-safe IPAM/VNI allocation for cluster-session networks.

Allocation state lives in etcd under ``network/ipam/*`` and is claimed with
compare-and-swap transactions, replacing Swarm's internal global IPAM. See
proposals/BEP-1055/control-plane.md.

NOTE: This is a P1 skeleton. Allocation bodies are implemented in P2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd

DEFAULT_IPAM_POOL = "10.128.0.0/12"
DEFAULT_BLOCK_PREFIXLEN = 24
DEFAULT_VNI_RANGE = (4096, 16777215)


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

    async def acquire(self) -> str:
        """Claim the first free block via CAS and return its CIDR."""
        raise NotImplementedError("BEP-1055 P2")

    async def release(self, subnet: str) -> None:
        raise NotImplementedError("BEP-1055 P2")


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

    async def acquire(self) -> int:
        raise NotImplementedError("BEP-1055 P2")

    async def release(self, vni: int) -> None:
        raise NotImplementedError("BEP-1055 P2")
