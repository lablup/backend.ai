"""Contract guards for the BEP-1055 P1 skeletons.

These assert the skeletons are inert (raise NotImplementedError with the P2 marker)
rather than silently appearing to work. They are replaced by real allocation tests in P2.
"""

from typing import cast

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.network.cni import CNINetworkPlugin
from ai.backend.manager.network.ipam import (
    DEFAULT_BLOCK_PREFIXLEN,
    DEFAULT_IPAM_POOL,
    DEFAULT_VNI_RANGE,
    SubnetAllocator,
    VNIAllocator,
)

_ETCD = cast(AsyncEtcd, object())


class TestSubnetAllocator:
    def test_instantiates_with_defaults(self) -> None:
        allocator = SubnetAllocator(_ETCD)
        assert allocator._pool == DEFAULT_IPAM_POOL
        assert allocator._block_prefixlen == DEFAULT_BLOCK_PREFIXLEN

    async def test_acquire_is_not_yet_implemented(self) -> None:
        allocator = SubnetAllocator(_ETCD)
        with pytest.raises(NotImplementedError):
            await allocator.acquire()

    async def test_release_is_not_yet_implemented(self) -> None:
        allocator = SubnetAllocator(_ETCD)
        with pytest.raises(NotImplementedError):
            await allocator.release("10.128.1.0/24")


class TestVNIAllocator:
    def test_instantiates_with_defaults(self) -> None:
        allocator = VNIAllocator(_ETCD)
        assert allocator._vni_range == DEFAULT_VNI_RANGE

    async def test_acquire_is_not_yet_implemented(self) -> None:
        allocator = VNIAllocator(_ETCD)
        with pytest.raises(NotImplementedError):
            await allocator.acquire()


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
