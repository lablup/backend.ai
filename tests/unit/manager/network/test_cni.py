"""Tests for the BEP-1078 control-plane pieces.

IPAM allocators are tested against an in-memory fake that models the etcd
compare-and-swap boundary (``put_if_absent``/``delete``); CAS atomicity itself is
delegated to etcd and verified separately against a live cluster. CNINetworkPlugin
create/destroy remain contract guards until P2 fills them in.
"""

import asyncio
import ipaddress
import json
from typing import Any, cast

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.network.types import (
    OVERLAY_ENCRYPTION_PROFILE,
    NetworkBackendKind,
    mac_for_ip,
)
from ai.backend.manager.errors.network import (
    ForcedBackendUnsupported,
    NetworkBackendMismatch,
    NetworkPoolExhausted,
    OverlayTeardownPending,
    RequestedSubnetInvalid,
    RequestedSubnetUnavailable,
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

    async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
        if self.store.get(key) != expected:
            return False
        del self.store[key]
        return True

    async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
        head = prefix.rstrip("/") + "/"
        return {
            key[len(head) :]: value for key, value in self.store.items() if key.startswith(head)
        }

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
        await allocator.release(first, "s1")
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
        await allocator.release(v, "s1")
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

    async def test_wide_block_skips_subnet_that_overlaps_a_narrow_one(self) -> None:
        # A /24 is taken; a later 300-endpoint session needs a /23. The /23 at the pool's
        # start (10.128.0.0/23) contains the taken /24, so it must be skipped rather than
        # allocated on top of it.
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        assert await allocator.acquire("s1") == "10.128.0.0/24"
        wide = await allocator.acquire("s2", host_count=300)
        assert wide == "10.128.2.0/23"
        assert not ipaddress.ip_network(wide).overlaps(ipaddress.ip_network("10.128.0.0/24"))

    async def test_narrow_block_skips_unit_owned_by_a_wide_one(self) -> None:
        # The reverse order: a /23 is taken first, then default /24 requests must land past it.
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        assert await allocator.acquire("s1", host_count=300) == "10.128.0.0/23"
        # both /24 units of the /23 are owned, so the next /24 is 10.128.2.0/24
        assert await allocator.acquire("s2") == "10.128.2.0/24"

    async def test_release_of_wide_block_frees_every_unit(self) -> None:
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        wide = await allocator.acquire("s1", host_count=300)
        await allocator.release(wide, "s1")
        # every /24 unit is free again, so a /24 request reuses the block's start
        assert await allocator.acquire("s2") == "10.128.0.0/24"
        assert await allocator.acquire("s3") == "10.128.1.0/24"


class TestExplicitSubnet:
    async def test_requested_subnet_is_claimed_verbatim(self) -> None:
        allocator = _subnet_allocator(FakeEtcd())
        # like `docker network create --subnet`: the exact block is honored, not auto-picked
        assert await allocator.acquire("s1", subnet="10.128.5.0/24") == "10.128.5.0/24"

    async def test_requested_wide_subnet_claims_all_units(self) -> None:
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        assert await allocator.acquire("s1", subnet="10.128.4.0/23") == "10.128.4.0/23"
        # both /24 units are now owned, so an auto /24 lands past them
        assert await allocator.acquire("s2") == "10.128.0.0/24"

    async def test_overlap_with_existing_is_a_hard_failure(self) -> None:
        # unlike auto mode (which skips), an explicit request overlapping a taken block errors
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        await allocator.acquire("s1")  # 10.128.0.0/24
        with pytest.raises(RequestedSubnetUnavailable):
            await allocator.acquire("s2", subnet="10.128.0.0/23")  # contains the taken /24
        # the failed request left nothing behind: the free /24 unit is still claimable
        assert await allocator.acquire("s3", subnet="10.128.1.0/24") == "10.128.1.0/24"

    async def test_subnet_outside_pool_is_rejected(self) -> None:
        allocator = _subnet_allocator(FakeEtcd())
        with pytest.raises(RequestedSubnetInvalid):
            await allocator.acquire("s1", subnet="192.168.0.0/24")

    async def test_misaligned_subnet_is_rejected(self) -> None:
        allocator = _subnet_allocator(FakeEtcd())
        with pytest.raises(RequestedSubnetInvalid):
            # host bits set for a /23 (10.128.1.0 is not a /23 boundary)
            await allocator.acquire("s1", subnet="10.128.1.0/23")

    async def test_subnet_narrower_than_unit_is_rejected(self) -> None:
        allocator = _subnet_allocator(FakeEtcd())  # unit block is /24
        with pytest.raises(RequestedSubnetInvalid):
            await allocator.acquire("s1", subnet="10.128.0.0/26")


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
        ip, mac = await alloc.assign(
            "s1", "c1", "10.128.5.0/24", agent_id="a1", cluster_hostname="main1"
        )
        rec = json.loads(etcd.store["network/session/s1/endpoints/c1"])
        assert rec == {
            "ip": ip,
            "mac": mac,
            "agent_id": "a1",
            "container_id": "c1",
            "cluster_hostname": "main1",
        }

    async def test_endpoint_record_without_hostname_is_null(self) -> None:
        # cluster_hostname is optional on the wire: an endpoint assigned without a name records
        # null, and EndpointAddr.from_etcd_payload decodes it back to None (backward-compatible).
        etcd = FakeEtcd()
        alloc = EndpointAllocator(cast(AsyncEtcd, etcd))
        await alloc.assign("s1", "c1", "10.128.5.0/24", agent_id="a1")
        rec = json.loads(etcd.store["network/session/s1/endpoints/c1"])
        assert rec["cluster_hostname"] is None

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
    def test_no_forced_backend_defaults_to_vxlan(self) -> None:
        # Multi-node cluster sessions use the portable vxlan overlay unless the operator pins one.
        plugin = _plugin_with(FakeEtcd())
        assert plugin._select_backend(None) is NetworkBackendKind.VXLAN

    def test_forced_vxlan_wins(self) -> None:
        plugin = _plugin_with(FakeEtcd())
        assert plugin._select_backend(NetworkBackendKind.VXLAN) is NetworkBackendKind.VXLAN

    def test_forced_bridge_is_rejected(self) -> None:
        # bridge is node-local (single-node); this control plane only serves multi-node sessions,
        # whose IPs are centrally assigned over an overlay. Pinning bridge would produce an
        # /etc/hosts naming overlay IPs no container holds, so it is refused up-front.
        plugin = _plugin_with(FakeEtcd())
        with pytest.raises(ForcedBackendUnsupported):
            plugin._select_backend(NetworkBackendKind.BRIDGE)


def _encryption_capable(etcd: FakeEtcd, *agent_ids: str) -> None:
    """Publish caps saying these agents speak the current overlay encryption profile.

    Needed by any test with member agents that is not ABOUT encryption: the default policy is
    `required`, so a member that cannot encrypt refuses the session -- which is the point.
    """
    for agent_id in agent_ids:
        etcd.store[f"network/agent/{agent_id}/caps"] = json.dumps({
            "tunnel_offload": False,
            "backends": ["vxlan"],
            "readiness": [],
            "encryption_profiles": [OVERLAY_ENCRYPTION_PROFILE],
        })


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

    async def test_vxlan_overlay_mtu_subtracts_the_encapsulation_overhead(self) -> None:
        # The value handed to every kernel is the OVERLAY MTU: underlay - 50. Handing the underlay
        # 1500 straight through (as this used to) lets a 1500-byte frame reach the 1450-MTU vxlan
        # port, where it is dropped with no ICMP — a PMTUD black hole that hangs NCCL/mpirun.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "encryption": False}
        )
        assert info.options["mtu"] == 1450  # 1500 underlay - 50 VXLAN overhead
        assert json.loads(etcd.store["network/session/s1/meta"])["mtu"] == 1450

    async def test_overlay_encryption_is_on_by_default(self) -> None:
        # Without it a multi-node session's traffic crosses the operator's underlay as plain
        # VXLAN, readable and injectable by anything on the path between two nodes. A default that
        # has to be found in the documentation is a default that is not set.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        key = info.options["encryption_key"]
        assert isinstance(key, str) and len(key) == 64
        assert json.loads(etcd.store["network/session/s1/meta"])["encryption_key"] == key

    async def test_the_default_leaves_room_for_the_esp_overhead(self) -> None:
        # The MTU the manager publishes is what the agent builds the devices with, so it has to
        # account for the encryption the same default just turned on.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        assert info.options["mtu"] == 1500 - 50 - 38
        assert json.loads(etcd.store["network/session/s1/meta"])["mtu"] == 1500 - 50 - 38

    async def test_an_operator_can_still_turn_it_off(self) -> None:
        etcd = FakeEtcd()
        plugin = CNINetworkPlugin({"overlay-encryption": False}, {})
        plugin._etcd = cast(AsyncEtcd, etcd)
        plugin._subnet_allocator = SubnetAllocator(cast(AsyncEtcd, etcd))
        plugin._vni_allocator = VNIAllocator(cast(AsyncEtcd, etcd))
        plugin._endpoint_allocator = EndpointAllocator(cast(AsyncEtcd, etcd))
        info = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        assert info.options["encryption_key"] is None
        assert json.loads(etcd.store["network/session/s1/meta"])["encryption_key"] is None

    async def test_a_per_network_request_still_overrides_an_operator_who_turned_it_off(
        self,
    ) -> None:
        etcd = FakeEtcd()
        plugin = CNINetworkPlugin({"overlay-encryption": False}, {})
        plugin._etcd = cast(AsyncEtcd, etcd)
        plugin._subnet_allocator = SubnetAllocator(cast(AsyncEtcd, etcd))
        plugin._vni_allocator = VNIAllocator(cast(AsyncEtcd, etcd))
        plugin._endpoint_allocator = EndpointAllocator(cast(AsyncEtcd, etcd))
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "encryption": True}
        )
        assert info.options["encryption_key"] is not None

    async def test_per_network_encryption_request_generates_key(self) -> None:
        # The caller can opt a single session into encryption; a fresh 64-hex key lands in the meta,
        # and the overlay MTU drops further to leave room for the ESP overhead.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "encryption": True}
        )
        key = info.options["encryption_key"]
        assert isinstance(key, str) and len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)
        assert info.options["mtu"] == 1500 - 50 - 38  # underlay - VXLAN - ESP overhead
        assert json.loads(etcd.store["network/session/s1/meta"])["encryption_key"] == key

    async def test_the_operator_default_can_be_stated_explicitly(self) -> None:
        # Setting it to the value it already has must not change anything.
        etcd = FakeEtcd()
        plugin = CNINetworkPlugin({"overlay-encryption": True}, {})
        plugin._etcd = cast(AsyncEtcd, etcd)
        plugin._subnet_allocator = SubnetAllocator(cast(AsyncEtcd, etcd))
        plugin._vni_allocator = VNIAllocator(cast(AsyncEtcd, etcd))
        plugin._endpoint_allocator = EndpointAllocator(cast(AsyncEtcd, etcd))
        info = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        assert info.options["encryption_key"] is not None

    async def test_per_network_request_overrides_operator_default(self) -> None:
        # An explicit per-network encryption=False wins over the operator default being on.
        etcd = FakeEtcd()
        plugin = CNINetworkPlugin({"overlay-encryption": True}, {})
        plugin._etcd = cast(AsyncEtcd, etcd)
        plugin._subnet_allocator = SubnetAllocator(cast(AsyncEtcd, etcd))
        plugin._vni_allocator = VNIAllocator(cast(AsyncEtcd, etcd))
        plugin._endpoint_allocator = EndpointAllocator(cast(AsyncEtcd, etcd))
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "encryption": False}
        )
        assert info.options["encryption_key"] is None

    async def test_forced_bridge_backend_is_rejected_before_any_allocation(self) -> None:
        # bridge cannot serve a multi-node session (this control plane's only caller); the
        # request is refused up-front, so no subnet/VNI/meta is claimed and nothing leaks.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        with pytest.raises(ForcedBackendUnsupported):
            await plugin.create_network(identifier="s2", options={"forced_backend": "bridge"})
        assert etcd.store == {}

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
        _encryption_capable(etcd, "a1", "a2")
        plugin = _plugin_with(etcd)
        await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
        )
        # each agent's member is written up-front so reconcile-at-start finds every peer
        m1 = json.loads(etcd.store["network/session/s1/members/a1"])
        m2 = json.loads(etcd.store["network/session/s1/members/a2"])
        assert m1 == {
            "host_ip": "192.168.105.7",
            "vtep_ip": "192.168.105.7",
            # Not an acknowledgement: nothing on that node has been touched yet, so this record
            # must not hold the session's VNI back at teardown.
            "joined": False,
        }
        assert m2["vtep_ip"] == "192.168.105.8"
        assert m2["joined"] is False

    async def test_preseed_skips_agents_without_published_vtep(self) -> None:
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/vtep"] = "192.168.105.7"  # a2 has not published a VTEP
        _encryption_capable(etcd, "a1", "a2")
        plugin = _plugin_with(etcd)
        await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
        )
        assert "network/session/s1/members/a1" in etcd.store

    async def test_partial_failure_rolls_back_and_retry_reuses_block(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        opts = {
            "forced_backend": "vxlan",
            "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
        }
        # First create fails mid-way (after subnet + VNI + meta are claimed, during endpoint
        # assignment). Everything claimed must be rolled back.
        calls = {"n": 0}
        real_assign = plugin._endpoint_allocator.assign

        async def flaky_assign(*args: Any, **kwargs: Any) -> tuple[str, str]:
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("boom")
            return await real_assign(*args, **kwargs)

        monkeypatch.setattr(plugin._endpoint_allocator, "assign", flaky_assign)

        with pytest.raises(RuntimeError):
            await plugin.create_network(identifier="s1", options=opts)
        # every session key deleted, and the subnet + VNI blocks released (not leaked)
        assert not any(k.startswith("network/session/s1/") for k in etcd.store)
        assert not any(k.startswith("network/ipam/allocated/") for k in etcd.store)
        assert not any(k.startswith("network/ipam/vni/") for k in etcd.store)

        # a retry re-acquires the SAME first block/VNI rather than consuming fresh ones
        info = await plugin.create_network(identifier="s1", options=opts)
        assert info.options["subnet"] == "10.128.0.0/24"  # first block, reused
        assert info.options["vni"] == 4096  # first VNI, reused
        # a2 falls back to self-publish + watch convergence (no seed written)
        assert "network/session/s1/members/a2" not in etcd.store


class TestMemberBackendCompat:
    async def test_containerd_member_ok(self) -> None:
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/backend"] = "containerd"
        _encryption_capable(etcd, "a1")
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "member_agents": ["a1"]}
        )
        assert info.options["backend"] == "vxlan"

    async def test_a_docker_member_is_accepted(self) -> None:
        # Docker serves the cni driver too: the vxlan device is moved into the container's netns
        # by PID, which is a kernel operation and not a containerd one.
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/backend"] = "docker"
        _encryption_capable(etcd, "a1")
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "member_agents": ["a1"]}
        )
        assert info.options["backend"] == "vxlan"

    async def test_a_kubernetes_member_still_raises_mismatch(self) -> None:
        # The check itself must keep working — this is the backend that genuinely cannot serve it.
        etcd = FakeEtcd()
        etcd.store["network/agent/a1/backend"] = "kubernetes"
        plugin = _plugin_with(etcd)
        with pytest.raises(NetworkBackendMismatch):
            await plugin.create_network(
                identifier="s1", options={"forced_backend": "vxlan", "member_agents": ["a1"]}
            )

    async def test_unpublished_backend_is_allowed(self) -> None:
        # safe before the agent publish path is wired: unknown -> allowed
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
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

    async def test_a_node_that_has_not_confirmed_teardown_holds_the_vni(self) -> None:
        """A member record the AGENT wrote means that node may still hold this VNI's devices,
        XFRM state and firewall rules. Handing the VNI on then gives the next session a
        stranger's rules, and lets the laggard's retry tear down the new session's data plane.

        It RAISES rather than returning: the caller retries on failure and on nothing else, so a
        quiet return would strand the allocation the moment one node lagged by a tick.
        """
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        etcd.store["network/session/s1/members/i-slow"] = json.dumps({
            "host_ip": "10.0.0.1",
            "vtep_ip": "10.0.0.1",
            "joined": True,
        })

        with pytest.raises(OverlayTeardownPending):
            await plugin.destroy_network("s1")
        assert any(k.startswith("network/ipam/vni/") for k in etcd.store)
        # and the session's own keys stay, so the retry can finish the job
        assert any(k.startswith("network/session/s1") for k in etcd.store)

    async def test_the_release_happens_once_the_last_node_confirms(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        etcd.store["network/session/s1/members/i-slow"] = json.dumps({
            "host_ip": "10.0.0.1",
            "vtep_ip": "10.0.0.1",
            "joined": True,
        })
        with pytest.raises(OverlayTeardownPending):
            await plugin.destroy_network("s1")

        del etcd.store["network/session/s1/members/i-slow"]
        await plugin.destroy_network("s1")
        assert not any(k.startswith("network/ipam/vni/") for k in etcd.store)
        assert not any(k.startswith("network/session/s1") for k in etcd.store)

    async def test_a_preseeded_member_does_not_hold_the_vni(self) -> None:
        """The pre-seed says which nodes are EXPECTED to take part, written before any of them has
        touched the host. Counting it as an acknowledgement would hold every session's allocation
        forever on a node that never received a kernel."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        etcd.store["network/session/s1/members/i-expected"] = json.dumps({
            "host_ip": "10.0.0.9",
            "vtep_ip": "10.0.0.9",
            "joined": False,
        })

        await plugin.destroy_network("s1")
        assert not any(k.startswith("network/ipam/vni/") for k in etcd.store)


class TestAllocationOwnership:
    """An unconditional release frees whatever holds the key NOW. After a reuse that is the next
    session's claim, and dropping it hands the same resource to a third -- two live sessions on
    one VNI, where either one's teardown removes the other's rules and devices."""

    async def test_a_vni_reclaimed_by_another_session_is_not_released(self) -> None:
        etcd = FakeEtcd()
        allocator = _vni_allocator(etcd, vni_range=(4096, 4098))
        vni = await allocator.acquire("s1")
        await allocator.release(vni, "s1")
        assert await allocator.acquire("s2") == vni  # reused

        assert await allocator.release(vni, "s1") is False  # s1 retrying its teardown
        assert etcd.store[f"network/ipam/vni/{vni}"] == json.dumps({"session_id": "s2"})

    async def test_releasing_a_vni_it_owns_succeeds(self) -> None:
        etcd = FakeEtcd()
        allocator = _vni_allocator(etcd, vni_range=(4096, 4098))
        vni = await allocator.acquire("s1")
        assert await allocator.release(vni, "s1") is True

    async def test_a_subnet_reclaimed_by_another_session_is_not_released(self) -> None:
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        subnet = await allocator.acquire("s1")
        await allocator.release(subnet, "s1")
        assert await allocator.acquire("s2") == subnet

        assert await allocator.release(subnet, "s1") is False
        assert any(
            json.loads(v).get("session_id") == "s2"
            for k, v in etcd.store.items()
            if k.startswith("network/ipam/allocated/")
        )

    async def test_releasing_a_subnet_it_owns_succeeds(self) -> None:
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        subnet = await allocator.acquire("s1")
        assert await allocator.release(subnet, "s1") is True


class TestEncryptingOnlyWhereEveryNodeCan:
    """The two ends of an ESP tunnel must agree on all of it: an agent that cannot do ESN cannot
    decrypt what one that can sends, so a session mixing versions comes up carrying nothing.

    Before encryption was the default that could not happen -- an operator turned it on once the
    nodes were ready. Now it is what a rolling upgrade produces on its own."""

    def _old(self, etcd: FakeEtcd, *agent_ids: str) -> None:
        """An agent from before the profile existed: it publishes caps, but not that field."""
        for agent_id in agent_ids:
            etcd.store[f"network/agent/{agent_id}/caps"] = json.dumps({
                "tunnel_offload": False,
                "backends": ["vxlan"],
                "readiness": [],
            })

    def _with_policy(self, etcd: FakeEtcd, policy: object) -> CNINetworkPlugin:
        plugin = CNINetworkPlugin({"overlay-encryption": policy}, {})
        plugin._etcd = cast(AsyncEtcd, etcd)
        plugin._subnet_allocator = SubnetAllocator(cast(AsyncEtcd, etcd))
        plugin._vni_allocator = VNIAllocator(cast(AsyncEtcd, etcd))
        plugin._endpoint_allocator = EndpointAllocator(cast(AsyncEtcd, etcd))
        return plugin

    async def test_every_node_capable_encrypts(self) -> None:
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1", "a2")
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
        )
        assert info.options["encryption_key"] is not None

    async def test_the_default_refuses_rather_than_downgrading(self) -> None:
        # The regression this class exists for. An operator who did not touch the setting gets
        # encryption; a node that cannot manage it is an error naming the node, not a plaintext
        # overlay and a log line nobody was reading.
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        self._old(etcd, "a2")
        plugin = _plugin_with(etcd)
        with pytest.raises(NetworkBackendMismatch, match="a2"):
            await plugin.create_network(
                identifier="s1",
                options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
            )

    async def test_an_explicit_true_refuses_too(self) -> None:
        # `true` was written by somebody who meant "these sessions are confidential".
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        self._old(etcd, "a2")
        plugin = self._with_policy(etcd, True)
        with pytest.raises(NetworkBackendMismatch):
            await plugin.create_network(
                identifier="s1",
                options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
            )

    async def test_required_refuses_a_node_that_published_nothing(self) -> None:
        # Silence is consent everywhere else in `pairing`; here it is an agent from before the
        # contract, and encrypting anyway is the failure this check exists for.
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        plugin = self._with_policy(etcd, "required")
        with pytest.raises(NetworkBackendMismatch, match="published no network capabilities"):
            await plugin.create_network(
                identifier="s1",
                options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
            )

    async def test_required_refuses_an_unreadable_record(self) -> None:
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        etcd.store["network/agent/a2/caps"] = "{not json"
        plugin = self._with_policy(etcd, "required")
        with pytest.raises(NetworkBackendMismatch, match="cannot read"):
            await plugin.create_network(
                identifier="s1",
                options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
            )

    async def test_required_refuses_an_unknown_profile(self) -> None:
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        etcd.store["network/agent/a2/caps"] = json.dumps({
            "tunnel_offload": False,
            "backends": ["vxlan"],
            "readiness": [],
            "encryption_profiles": ["esp-aesgcm-esn-v99"],
        })
        plugin = self._with_policy(etcd, "required")
        with pytest.raises(NetworkBackendMismatch, match="esp-aesgcm-esn-v99"):
            await plugin.create_network(
                identifier="s1",
                options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
            )

    async def test_prefer_is_what_falls_back(self) -> None:
        # The rolling-upgrade setting, and the only one that yields a plaintext overlay from a
        # cluster that asked for encryption. Chosen deliberately, by name.
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        self._old(etcd, "a2")
        plugin = self._with_policy(etcd, "prefer")
        info = await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
        )
        assert info.options["encryption_key"] is None
        assert info.options["mtu"] == 1450, "and it gets the unencrypted MTU to match"

    async def test_prefer_still_encrypts_where_it_can(self) -> None:
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1", "a2")
        plugin = self._with_policy(etcd, "prefer")
        info = await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1", "a2"]},
        )
        assert info.options["encryption_key"] is not None

    async def test_a_caller_that_asked_for_encryption_overrides_prefer(self) -> None:
        # It stated a requirement; `prefer` is the operator's fallback, not the caller's.
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        self._old(etcd, "a2")
        plugin = self._with_policy(etcd, "prefer")
        with pytest.raises(NetworkBackendMismatch):
            await plugin.create_network(
                identifier="s1",
                options={
                    "forced_backend": "vxlan",
                    "member_agents": ["a1", "a2"],
                    "encryption": True,
                },
            )

    async def test_disabled_asks_nothing_of_the_nodes(self) -> None:
        etcd = FakeEtcd()
        self._old(etcd, "a1")
        plugin = self._with_policy(etcd, "disabled")
        info = await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1"]},
        )
        assert info.options["encryption_key"] is None

    async def test_a_per_session_opt_out_asks_nothing_either(self) -> None:
        etcd = FakeEtcd()
        self._old(etcd, "a1")
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1",
            options={"forced_backend": "vxlan", "member_agents": ["a1"], "encryption": False},
        )
        assert info.options["encryption_key"] is None


def _pool_claims(etcd: FakeEtcd) -> list[str]:
    """Every subnet/VNI claim standing in the shared pool."""
    return sorted(
        key
        for key in etcd.store
        if key.startswith(("network/ipam/allocated/", "network/ipam/vni/"))
    )


class TestCreatingTheSameSessionTwice:
    """A session start that fails downstream is retried with the same session id.

    The retry must land on the allocation the first attempt made. A second subnet and VNI would
    be claimed by a session that no longer references them, and `destroy_network` releases only
    what the meta records -- so the first pair would stay allocated for the cluster's lifetime.
    """

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    async def test_the_retry_gets_the_same_subnet_vni_and_address(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        first = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        second = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        assert second.options["subnet"] == first.options["subnet"]
        assert second.options["vni"] == first.options["vni"]
        assert second.options["endpoint_ips"] == first.options["endpoint_ips"]

    async def test_it_claims_nothing_further_from_the_pool(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        after_first = _pool_claims(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        assert _pool_claims(etcd) == after_first

    async def test_a_kernel_added_between_the_attempts_still_gets_an_address(self) -> None:
        # The first attempt assigned k1 only; the retry carries both kernels.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        second = await plugin.create_network(
            identifier="s1",
            options={
                "forced_backend": "vxlan",
                "endpoints": [
                    {"container_id": "k1", "agent_id": "a1"},
                    {"container_id": "k2", "agent_id": "a2"},
                ],
            },
        )
        ips = second.options["endpoint_ips"]
        assert set(ips) == {"k1", "k2"}
        assert ips["k1"] != ips["k2"]


class TestACreateThatNeverFinished:
    async def test_cancellation_gives_the_subnet_and_vni_back(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        started = asyncio.Event()

        async def never_returns(session_id: str) -> int:
            started.set()
            await asyncio.sleep(60)
            raise AssertionError("unreachable")

        plugin._vni_allocator.acquire = never_returns  # type: ignore[method-assign]
        task = asyncio.create_task(
            plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        )
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # `except Exception` would have let the cancellation past the rollback.
        assert _pool_claims(etcd) == []

    async def test_a_subnet_left_claimed_is_reused_not_orphaned(self) -> None:
        # The rollback itself can fail (etcd unreachable), leaving the block claimed with no
        # session meta pointing at it. The next attempt must recognise its own claim.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        stranded = await plugin._subnet_allocator.acquire("s1")
        info = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        assert info.options["subnet"] == stranded
        assert len([k for k in etcd.store if k.startswith("network/ipam/allocated/")]) == 1

    async def test_a_vni_left_claimed_is_reused_not_orphaned(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        stranded = await plugin._vni_allocator.acquire("s1")
        info = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        assert info.options["vni"] == stranded
        assert len([k for k in etcd.store if k.startswith("network/ipam/vni/")]) == 1
