"""Tests for the BEP-1058 control-plane pieces.

IPAM allocators are tested against an in-memory fake that models the etcd
compare-and-swap boundary (``put_if_absent``/``delete``); CAS atomicity itself is
delegated to etcd and verified separately against a live cluster. CNINetworkPlugin
create/destroy remain contract guards until P2 fills them in.
"""

import json
from typing import Any, cast

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.network.types import NetworkBackendKind, mac_for_ip
from ai.backend.manager.errors.network import (
    NetworkBackendMismatch,
    NetworkPoolExhausted,
    VNIPoolExhausted,
)
from ai.backend.manager.network.cni import CNINetworkPlugin
from ai.backend.manager.network.ipam import (
    EndpointAllocator,
    SubnetAllocator,
    VNIAllocator,
    _prefix_for_hosts,
)


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


class TestPrefixForHosts:
    def test_small_cluster_keeps_default_prefix(self) -> None:
        # up to 254 endpoints fit in a /24
        assert _prefix_for_hosts(1, default_prefixlen=24, floor_prefixlen=12) == 24
        assert _prefix_for_hosts(254, default_prefixlen=24, floor_prefixlen=12) == 24

    def test_over_254_widens_to_23(self) -> None:
        # 255 endpoints no longer fit in a /24 (254 usable) -> /23 (510 usable)
        assert _prefix_for_hosts(255, default_prefixlen=24, floor_prefixlen=12) == 23
        assert _prefix_for_hosts(510, default_prefixlen=24, floor_prefixlen=12) == 23

    def test_widens_further_for_large_cluster(self) -> None:
        assert _prefix_for_hosts(1000, default_prefixlen=24, floor_prefixlen=12) == 22

    def test_bounded_by_pool_floor(self) -> None:
        # a request bigger than the pool cannot widen past the pool's own prefix
        assert _prefix_for_hosts(10**9, default_prefixlen=24, floor_prefixlen=12) == 12


class TestVariableSubnetSizing:
    async def test_host_count_sizes_the_block(self) -> None:
        allocator = _subnet_allocator(FakeEtcd())
        # 300 endpoints need a /23, not the default /24
        assert await allocator.acquire("s1", host_count=300) == "10.128.0.0/23"

    async def test_default_is_slash24(self) -> None:
        allocator = _subnet_allocator(FakeEtcd())
        assert await allocator.acquire("s1") == "10.128.0.0/24"


class TestMacForIp:
    def test_stable_and_ip_encoded(self) -> None:
        assert mac_for_ip("10.128.5.2") == "02:42:0a:80:05:02"

    def test_distinct_ips_distinct_macs(self) -> None:
        assert mac_for_ip("10.128.5.2") != mac_for_ip("10.128.5.3")


class TestEndpointAllocator:
    async def test_assigns_disjoint_ips_across_endpoints(self) -> None:
        etcd = FakeEtcd()
        alloc = EndpointAllocator(cast(AsyncEtcd, etcd))
        ip1, mac1 = await alloc.assign("s1", "c1", "10.128.5.0/24", agent_id="a1")
        ip2, mac2 = await alloc.assign("s1", "c2", "10.128.5.0/24", agent_id="a2")
        # central assignment guarantees disjoint IPs (the whole point vs host-local)
        assert ip1 == "10.128.5.1"
        assert ip2 == "10.128.5.2"
        assert mac1 == mac_for_ip(ip1)
        assert ip1 != ip2 and mac1 != mac2

    async def test_endpoint_record_written(self) -> None:
        etcd = FakeEtcd()
        alloc = EndpointAllocator(cast(AsyncEtcd, etcd))
        ip, mac = await alloc.assign("s1", "c1", "10.128.5.0/24", agent_id="a1")
        rec = json.loads(etcd.store["network/session/s1/endpoints/c1"])
        assert rec == {"ip": ip, "mac": mac, "agent_id": "a1", "container_id": "c1"}

    async def test_release_frees_ip_for_reuse(self) -> None:
        etcd = FakeEtcd()
        alloc = EndpointAllocator(cast(AsyncEtcd, etcd))
        ip1, _ = await alloc.assign("s1", "c1", "10.128.5.0/24", agent_id="a1")
        await alloc.release("s1", "c1", ip1)
        ip2, _ = await alloc.assign("s1", "c2", "10.128.5.0/24", agent_id="a2")
        assert ip2 == ip1

    async def test_exhaustion_raises(self) -> None:
        etcd = FakeEtcd()
        alloc = EndpointAllocator(cast(AsyncEtcd, etcd))
        # /30 has 2 usable hosts -> 3rd assign exhausts
        await alloc.assign("s1", "c1", "10.128.5.0/30", agent_id="a1")
        await alloc.assign("s1", "c2", "10.128.5.0/30", agent_id="a2")
        with pytest.raises(NetworkPoolExhausted):
            await alloc.assign("s1", "c3", "10.128.5.0/30", agent_id="a1")


def _plugin_with(etcd: FakeEtcd) -> CNINetworkPlugin:
    """Build a plugin with the allocators wired to a fake etcd, bypassing init()."""
    plugin = CNINetworkPlugin({}, {})
    plugin._etcd = cast(AsyncEtcd, etcd)
    plugin._subnet_allocator = SubnetAllocator(cast(AsyncEtcd, etcd))
    plugin._vni_allocator = VNIAllocator(cast(AsyncEtcd, etcd))
    plugin._endpoint_allocator = EndpointAllocator(cast(AsyncEtcd, etcd))
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
            etcd.store[f"network/agent/{agent_id}/caps"] = json.dumps({"native_routing_ok": True})
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
        info = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
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
        info = await plugin.create_network(identifier="s2", options={"forced_backend": "host-gw"})
        assert info.options["backend"] == "host-gw"
        assert info.options["vni"] is None

    async def test_assigns_disjoint_endpoint_ips_and_records_them(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1",
            options={
                "forced_backend": "vxlan",
                "endpoints": [
                    {"container_id": "k1", "agent_id": "a1"},
                    {"container_id": "k2", "agent_id": "a2"},
                ],
            },
        )
        ips = info.options["endpoint_ips"]
        # each kernel gets a distinct overlay IP (central assignment, no host-local collision)
        assert ips["k1"] != ips["k2"]
        assert set(ips) == {"k1", "k2"}
        # recorded under endpoints/ with the owning agent (coordinator resolves VTEP from it)
        rec = json.loads(etcd.store["network/session/s1/endpoints/k2"])
        assert rec["agent_id"] == "a2" and rec["ip"] == ips["k2"]

    async def test_subnet_sized_by_endpoint_count(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        endpoints = [{"container_id": f"k{i}", "agent_id": "a1"} for i in range(300)]
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "endpoints": endpoints}
        )
        # 300 endpoints no longer fit a /24 -> widened to /23
        assert info.options["subnet"] == "10.128.0.0/23"

    async def test_preseeds_member_table_from_published_vteps(self) -> None:
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/vtep"] = "192.168.105.7"
        etcd.store["network/agent/a2/vtep"] = "192.168.105.8"
        plugin = _plugin_with(etcd)
        await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
        )
        # each agent's member is written up-front so reconcile-at-start finds every peer
        m1 = json.loads(etcd.store["network/session/s1/members/a1"])
        m2 = json.loads(etcd.store["network/session/s1/members/a2"])
        assert m1 == {"host_ip": "192.168.105.7", "vtep_ip": "192.168.105.7", "ip_range": None}
        assert m2["vtep_ip"] == "192.168.105.8"

    async def test_preseed_skips_agents_without_published_vtep(self) -> None:
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/vtep"] = "192.168.105.7"  # a2 has not published
        plugin = _plugin_with(etcd)
        await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
        )
        assert "network/session/s1/members/a1" in etcd.store
        # a2 falls back to self-publish + watch convergence (no seed written)
        assert "network/session/s1/members/a2" not in etcd.store

    async def test_host_gw_does_not_preseed_members(self) -> None:
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/vtep"] = "192.168.105.7"
        plugin = _plugin_with(etcd)
        await plugin.create_network(
            identifier="s2",
            options={"forced_backend": "host-gw", "member_agents": ["a1"]},
        )
        # VTEP-based pre-seed applies to vxlan only
        assert "network/session/s2/members/a1" not in etcd.store


class TestMemberBackendCompat:
    async def test_containerd_member_ok(self) -> None:
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/backend"] = "containerd"
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "member_agents": ["a1"]}
        )
        assert info.options["backend"] == "vxlan"

    async def test_docker_member_raises_mismatch(self) -> None:
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/backend"] = "docker"  # wrong backend under cni driver
        plugin = _plugin_with(etcd)
        with pytest.raises(NetworkBackendMismatch):
            await plugin.create_network(
                identifier="s1", options={"forced_backend": "vxlan", "member_agents": ["a1"]}
            )

    async def test_unpublished_backend_is_allowed(self) -> None:
        # safe before the agent publish path is wired: unknown -> allowed
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "member_agents": ["a1"]}
        )
        assert info.options["backend"] == "vxlan"


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
