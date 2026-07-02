"""Tests for the BEP-1055 control-plane pieces.

IPAM allocators are tested against an in-memory fake that models the etcd
compare-and-swap boundary (``put_if_absent``/``delete``); CAS atomicity itself is
delegated to etcd and verified separately against a live cluster. CNINetworkPlugin
create/destroy remain contract guards until P2 fills them in.
"""

import json
from typing import Any, cast

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.network.types import NetworkBackendKind
from ai.backend.manager.errors.network import NetworkPoolExhausted, VNIPoolExhausted
from ai.backend.manager.network.cni import CNINetworkPlugin
from ai.backend.manager.network.ipam import SubnetAllocator, VNIAllocator


class FakeEtcd:
    """In-memory stand-in modeling the etcd methods the control plane uses."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def put_if_absent(self, key: str, val: str, **kwargs: Any) -> bool:
        if key in self.store:
            return False
        self.store[key] = val
        return True

    async def put(self, key: str, val: str, **kwargs: Any) -> None:
        self.store[key] = val

    async def get(self, key: str, **kwargs: Any) -> str | None:
        return self.store.get(key)

    async def delete(self, key: str, **kwargs: Any) -> None:
        self.store.pop(key, None)

    async def delete_prefix(self, prefix: str, **kwargs: Any) -> None:
        for key in [k for k in self.store if k.startswith(prefix)]:
            del self.store[key]


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


def _plugin_with(etcd: FakeEtcd) -> CNINetworkPlugin:
    """Build a plugin with the allocators wired to a fake etcd, bypassing init()."""
    plugin = CNINetworkPlugin({}, {})
    plugin._etcd = cast(AsyncEtcd, etcd)
    plugin._subnet_allocator = SubnetAllocator(cast(AsyncEtcd, etcd))
    plugin._vni_allocator = VNIAllocator(cast(AsyncEtcd, etcd))
    return plugin


class TestSelectBackend:
    async def test_forced_backend_wins(self) -> None:
        plugin = _plugin_with(FakeEtcd())
        result = await plugin._select_backend(["a1"], NetworkBackendKind.VXLAN)
        assert result is NetworkBackendKind.VXLAN

    async def test_no_members_defaults_to_vxlan(self) -> None:
        plugin = _plugin_with(FakeEtcd())
        assert await plugin._select_backend([], None) is NetworkBackendKind.VXLAN

    async def test_all_native_selects_host_gw(self) -> None:
        etcd = FakeEtcd()
        for agent_id in ("a1", "a2"):
            etcd.store[f"network/agent/{agent_id}/caps"] = json.dumps(
                {"native_routing_ok": True}
            )
        plugin = _plugin_with(etcd)
        assert await plugin._select_backend(["a1", "a2"], None) is NetworkBackendKind.HOST_GW

    async def test_one_non_native_falls_back_to_vxlan(self) -> None:
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/caps"] = json.dumps({"native_routing_ok": True})
        etcd.store["network/agent/a2/caps"] = json.dumps({"native_routing_ok": False})
        plugin = _plugin_with(etcd)
        assert await plugin._select_backend(["a1", "a2"], None) is NetworkBackendKind.VXLAN

    async def test_missing_caps_falls_back_to_vxlan(self) -> None:
        plugin = _plugin_with(FakeEtcd())  # no caps published
        assert await plugin._select_backend(["a1"], None) is NetworkBackendKind.VXLAN


class TestCreateNetwork:
    def test_instantiates_with_no_forced_backend(self) -> None:
        plugin = CNINetworkPlugin({}, {})
        assert plugin._forced_backend is None

    async def test_vxlan_allocates_subnet_and_vni_and_writes_meta(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan"}
        )
        assert info.network_id == "s1"
        assert info.options["backend"] == "vxlan"
        assert info.options["subnet"] == "10.128.0.0/24"
        assert info.options["vni"] is not None
        # meta persisted
        raw = etcd.store["network/session/s1/meta"]
        assert json.loads(raw)["backend"] == "vxlan"

    async def test_host_gw_has_no_vni(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s2", options={"forced_backend": "host-gw"}
        )
        assert info.options["backend"] == "host-gw"
        assert info.options["vni"] is None


class TestDestroyNetwork:
    async def test_releases_subnet_and_vni_and_deletes_prefix(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        assert any(k.startswith("network/ipam/allocated/") for k in etcd.store)
        assert any(k.startswith("network/ipam/vni/") for k in etcd.store)

        await plugin.destroy_network("s1")
        assert not any(k.startswith("network/session/s1") for k in etcd.store)
        assert not any(k.startswith("network/ipam/allocated/") for k in etcd.store)
        assert not any(k.startswith("network/ipam/vni/") for k in etcd.store)

    async def test_missing_network_is_noop(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.destroy_network("does-not-exist")  # must not raise
