"""Tests for the BEP-1055 control-plane pieces.

IPAM allocators are tested against an in-memory fake that models the etcd
compare-and-swap boundary (``put_if_absent``/``delete``); CAS atomicity itself is
delegated to etcd and verified separately against a live cluster. CNINetworkPlugin
create/destroy remain contract guards until P2 fills them in.
"""

from typing import Any, cast

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.errors.network import NetworkPoolExhausted, VNIPoolExhausted
from ai.backend.manager.network.cni import CNINetworkPlugin
from ai.backend.manager.network.ipam import SubnetAllocator, VNIAllocator


class FakeEtcd:
    """In-memory stand-in modeling put_if_absent / delete semantics."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def put_if_absent(self, key: str, val: str, **kwargs: Any) -> bool:
        if key in self.store:
            return False
        self.store[key] = val
        return True

    async def delete(self, key: str, **kwargs: Any) -> None:
        self.store.pop(key, None)


def _subnet_allocator(etcd: FakeEtcd, **kwargs: Any) -> SubnetAllocator:
    return SubnetAllocator(cast(AsyncEtcd, etcd), **kwargs)


def _vni_allocator(etcd: FakeEtcd, **kwargs: Any) -> VNIAllocator:
    return VNIAllocator(cast(AsyncEtcd, etcd), **kwargs)


class TestSubnetAllocator:
    async def test_acquire_returns_first_block(self) -> None:
        allocator = _subnet_allocator(FakeEtcd())
        assert await allocator.acquire("s1") == "10.128.0.0/24"

    async def test_acquire_skips_taken_blocks(self) -> None:
        allocator = _subnet_allocator(FakeEtcd())
        first = await allocator.acquire("s1")
        second = await allocator.acquire("s2")
        assert first == "10.128.0.0/24"
        assert second == "10.128.1.0/24"

    async def test_release_frees_block_for_reuse(self) -> None:
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        first = await allocator.acquire("s1")
        await allocator.acquire("s2")
        await allocator.release(first)
        # first free block is again the released one
        assert await allocator.acquire("s3") == first

    async def test_exhaustion_raises(self) -> None:
        # /24 pool split into two /25 blocks -> third acquire exhausts.
        allocator = _subnet_allocator(FakeEtcd(), pool="10.0.0.0/24", block_prefixlen=25)
        await allocator.acquire("s1")
        await allocator.acquire("s2")
        with pytest.raises(NetworkPoolExhausted):
            await allocator.acquire("s3")


class TestVNIAllocator:
    async def test_acquire_returns_low_first(self) -> None:
        allocator = _vni_allocator(FakeEtcd(), vni_range=(4096, 4098))
        assert await allocator.acquire("s1") == 4096
        assert await allocator.acquire("s2") == 4097

    async def test_release_frees_vni_for_reuse(self) -> None:
        etcd = FakeEtcd()
        allocator = _vni_allocator(etcd, vni_range=(4096, 4098))
        v = await allocator.acquire("s1")
        await allocator.release(v)
        assert await allocator.acquire("s2") == v

    async def test_exhaustion_raises(self) -> None:
        allocator = _vni_allocator(FakeEtcd(), vni_range=(100, 101))
        await allocator.acquire("s1")
        await allocator.acquire("s2")
        with pytest.raises(VNIPoolExhausted):
            await allocator.acquire("s3")


class TestCNINetworkPlugin:
    def test_instantiates_with_no_forced_backend(self) -> None:
        plugin = CNINetworkPlugin({}, {})
        assert plugin._forced_backend is None

    async def test_create_network_is_not_yet_implemented(self) -> None:
        plugin = CNINetworkPlugin({}, {})
        with pytest.raises(NotImplementedError):
            await plugin.create_network(identifier="s1", options={"member_agents": ["a1"]})

    async def test_destroy_network_is_not_yet_implemented(self) -> None:
        plugin = CNINetworkPlugin({}, {})
        with pytest.raises(NotImplementedError):
            await plugin.destroy_network("s1")
