"""Tests for the BEP-1078 control-plane pieces.

IPAM allocators are tested against an in-memory fake that models the etcd
compare-and-swap boundary (``put_if_absent``/``delete``); CAS atomicity itself is
delegated to etcd and verified separately against a live cluster. CNINetworkPlugin
create/destroy remain contract guards until P2 fills them in.
"""

import asyncio
import ipaddress
import json
import time
from collections.abc import Mapping
from typing import Any, TypeVar, cast, override

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.network.keys import member_key, session_meta_key
from ai.backend.common.network.types import (
    OVERLAY_ENCRYPTION_PROFILE,
    Member,
    NetworkBackendKind,
    mac_for_ip,
)
from ai.backend.manager.errors.network import (
    EndpointSuperseded,
    ForcedBackendUnsupported,
    NetworkBackendMismatch,
    NetworkPoolExhausted,
    OverlayTeardownPending,
    RequestedSubnetInvalid,
    RequestedSubnetUnavailable,
    SessionCleanupPending,
    SessionRecordContested,
    SubnetClaimStranded,
    VNIPoolExhausted,
)
from ai.backend.manager.network import cni
from ai.backend.manager.network.cni import CNINetworkPlugin
from ai.backend.manager.network.ipam import (
    EndpointAllocator,
    SubnetAllocator,
    VNIAllocator,
    _allocated_key,
    _claim,
    _prefix_for_hosts,
)
from ai.backend.manager.plugin.network import NetworkInfo


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

    async def replace(self, key: str, initial_val: str, new_val: str, **kwargs: Any) -> bool:
        """etcd's compare-and-swap on the value: the write lands only over what was expected.

        Modelled because it is the fence the control plane rests on -- a manager that has been
        superseded must find out here rather than overwriting whoever succeeded it.
        """
        if self.store.get(key) != initial_val:
            return False
        self.store[key] = new_val
        return True

    async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
        if self.store.get(key) != expected:
            return False
        del self.store[key]
        return True

    async def compare_and_delete(
        self,
        key: str,
        expected: str,
        *,
        guards: Mapping[str, str | None],
        **kwargs: Any,
    ) -> bool:
        """Delete over the target's own bytes AND the state of the keys that made it garbage.

        Modelled because the reconciler rests on it: it decides a claim is an orphan by reading a
        session record, and between that read and the delete the record can appear and the claim
        be re-taken by the session it then names. A guard value of None means "must be absent".
        """
        if self.store.get(key) != expected:
            return False
        for guard_key, guard_val in guards.items():
            if guard_val is None:
                if guard_key in self.store:
                    return False
            elif self.store.get(guard_key) != guard_val:
                return False
        del self.store[key]
        return True

    async def compare_and_put(
        self,
        key: str,
        val: str,
        *,
        expected: str | None,
        guards: Mapping[str, str],
        **kwargs: Any,
    ) -> bool:
        """One store operation over the target AND the keys that make writing it legitimate.

        Modelled because a compare-and-swap on the target alone cannot express what a create
        needs: it still CREATES a key that is absent, and absent is what a teardown of the session
        just made it -- so the write attaches this create's state to a session that is not its.
        """
        if expected is None:
            if key in self.store:
                return False
        elif self.store.get(key) != expected:
            return False
        for guard_key, guard_val in guards.items():
            if self.store.get(guard_key) != guard_val:
                return False
        self.store[key] = val
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
            "generation": None,
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


_P = TypeVar("_P", bound=CNINetworkPlugin)


def _wire[P: CNINetworkPlugin](plugin: P, etcd: FakeEtcd) -> P:
    """Point a plugin's allocators at a fake etcd, bypassing init()."""
    plugin._etcd = cast(AsyncEtcd, etcd)
    plugin._subnet_allocator = SubnetAllocator(cast(AsyncEtcd, etcd))
    plugin._vni_allocator = VNIAllocator(cast(AsyncEtcd, etcd))
    plugin._endpoint_allocator = EndpointAllocator(cast(AsyncEtcd, etcd))
    return plugin


def _rebuilt_as(generation: str) -> str:
    """The record a rebuild of a session id actually leaves behind.

    `_claim_session` claims the id with a fresh record: an owner, a state, and the new
    incarnation. It names no subnet and no VNI -- those are written at publish, by the create
    that allocates them. Rewriting the generation of a PUBLISHED record instead would make one
    that names an allocation some other incarnation holds, which no path writes and which the
    sweeps read (rightly) as a live session on that allocation.
    """
    return json.dumps({
        "_owner": "another-manager",
        "_state": "creating",
        "_claimed_at": time.time(),
        "generation": generation,
    })


def _owed(plugin: CNINetworkPlugin) -> bool:
    """Read through a call so the checker does not narrow the attribute across a whole test."""
    return plugin._reconciliation_owed


def _plugin_with(etcd: FakeEtcd) -> CNINetworkPlugin:
    return _wire(CNINetworkPlugin({}, {}), etcd)


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
        info = await plugin.create_network(
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
            # Which incarnation of the session id it stands for, so a cleanup of an earlier one
            # cannot take it.
            "generation": info.options["generation"],
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


class _CountingCas(FakeEtcd):
    """Counts the guarded writes a claim attempt costs, so a scan that should have stopped is
    visible as a number rather than as a wait."""

    def __init__(self) -> None:
        super().__init__()
        self.cas = 0

    @override
    async def compare_and_put(self, key: str, val: str, **kwargs: Any) -> bool:
        self.cas += 1
        return await super().compare_and_put(key, val, **kwargs)


def _flat_claims(etcd: FakeEtcd) -> dict[str, str]:
    """The pool listing as the allocator reads it: unit key (quoted) -> claim bytes."""
    head = "network/ipam/allocated/"
    return {key[len(head) :]: value for key, value in etcd.store.items() if key.startswith(head)}


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

        class NeverReturns(VNIAllocator):
            @override
            async def acquire(
                self,
                session_id: str,
                generation: str | None = None,
                guards: Mapping[str, str] | None = None,
            ) -> int:
                started.set()
                await asyncio.sleep(60)
                raise AssertionError("unreachable")

        plugin._vni_allocator = NeverReturns(cast(AsyncEtcd, etcd))
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


class _GatedEtcd(FakeEtcd):
    """A store that holds the ALLOCATION prefix reads at a barrier, so two callers see one
    snapshot.

    That is the shape of the race: two managers both find no meta, and both go on to allocate.

    Scoped to the pool and the session's own subtree. A create reads other prefixes on the way in
    -- what earlier incarnations of the id still owe, for one -- and holding those at the barrier
    stops both callers before either reaches the race this models.
    """

    def __init__(self, gate: asyncio.Event) -> None:
        super().__init__()
        self._gate = gate

    @override
    async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
        found = await super().get_prefix(prefix, **kwargs)
        if prefix.startswith(("network/ipam", "network/session")):
            await self._gate.wait()
        return found


class TestTwoManagersCreatingOneSession:
    """C1. A session start can reach two managers at once -- an HA pair, or a retry landing
    elsewhere while the first is still running. Each allocation the losers walk away from is
    claimed by nobody's meta, and nothing ever frees it."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    async def _race(self) -> tuple[FakeEtcd, list[Any]]:
        gate = asyncio.Event()
        etcd = _GatedEtcd(gate)
        managers = [_plugin_with(etcd) for _ in range(2)]
        tasks = [
            asyncio.create_task(m.create_network(identifier="s1", options=dict(self._OPTIONS)))
            for m in managers
        ]
        await asyncio.sleep(0)
        gate.set()
        return etcd, list(await asyncio.gather(*tasks))

    async def test_both_get_the_same_allocation(self) -> None:
        _etcd, results = await self._race()
        first, second = results
        assert second.options["subnet"] == first.options["subnet"]
        assert second.options["vni"] == first.options["vni"]
        assert second.options["endpoint_ips"] == first.options["endpoint_ips"]

    async def test_the_pool_holds_exactly_one_of_each(self) -> None:
        etcd, _results = await self._race()
        blocks = [k for k in etcd.store if k.startswith("network/ipam/allocated/")]
        vnis = [k for k in etcd.store if k.startswith("network/ipam/vni/")]
        addresses = [k for k in etcd.store if k.startswith("network/session/s1/ipam/")]
        assert len(blocks) == 1, f"a block was claimed and abandoned: {sorted(blocks)}"
        assert len(vnis) == 1, f"a VNI was claimed and abandoned: {sorted(vnis)}"
        assert len(addresses) == 1, f"an address was claimed and abandoned: {sorted(addresses)}"

    async def test_what_the_meta_records_is_what_is_claimed(self) -> None:
        etcd, results = await self._race()
        meta = json.loads(etcd.store["network/session/s1/meta"])
        assert await _plugin_with(etcd)._subnet_allocator.holder(meta["subnet"]) == "s1"
        assert await _plugin_with(etcd)._vni_allocator.holder(int(meta["vni"])) == "s1"
        assert {r.options["subnet"] for r in results} == {meta["subnet"]}


class _GateOnGet(FakeEtcd):
    """A store that holds every single-key read at a barrier.

    That is the shape of the takeover race: two waiters read one record and each decides, on the
    strength of that same read, that the session is now theirs.
    """

    def __init__(self, gate: asyncio.Event) -> None:
        super().__init__()
        self._gate = gate

    @override
    async def get(self, key: str, **kwargs: Any) -> str | None:
        found = await super().get(key, **kwargs)
        await self._gate.wait()
        return found


_META_KEY = "network/session/s1/meta"


class TestASessionTakenFromItsCreator:
    """C5b. A create that is only slow and one that died look the same from outside, and the
    handover cannot tell them apart -- so it takes the session from both. A manager that has been
    superseded therefore has to find out at its next write: what it publishes over, rolls back and
    destroys is the record it still holds, or nothing at all."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    @staticmethod
    def _hand_over_at_once(monkeypatch: pytest.MonkeyPatch) -> None:
        """Take the session over on the first look, instead of a minute from now."""
        monkeypatch.setattr(cni, "_CREATE_HANDOVER_SEC", 0.0)

    async def _taken_over(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> tuple[FakeEtcd, CNINetworkPlugin, str, NetworkInfo]:
        """One manager claims the session and stalls; a second takes it over and finishes it.

        Returns the record the first one still believes it holds, and what the second published.
        """
        etcd = FakeEtcd()
        superseded = _plugin_with(etcd)
        held, published = await superseded._claim_session(cast(AsyncEtcd, etcd), "s1", "tok1", [])
        assert published is None
        self._hand_over_at_once(monkeypatch)
        info = await _plugin_with(etcd).create_network(identifier="s1", options=dict(self._OPTIONS))
        return etcd, superseded, held, info

    async def test_the_superseded_create_cannot_publish_over_the_new_owner(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        etcd, superseded, held, info = await self._taken_over(monkeypatch)
        with pytest.raises(SessionRecordContested):
            await superseded._publish(
                cast(AsyncEtcd, etcd),
                "s1",
                held,
                {"subnet": "10.128.9.0/24", "vni": 9999, "_owner": "tok1", "_state": "ready"},
            )
        # Not a word of the loser's is on the record -- including the "ready" that would have
        # handed its caller a subnet and a VNI the pool has given to the winner.
        meta = json.loads(etcd.store[_META_KEY])
        assert meta["subnet"] == info.options["subnet"]
        assert meta["vni"] == info.options["vni"]

    async def test_its_rollback_leaves_the_new_owner_whole(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        etcd, superseded, held, info = await self._taken_over(monkeypatch)
        await superseded._rollback_create(
            "s1", str(info.options["subnet"]), int(cast(int, info.options["vni"])), held
        )
        assert _META_KEY in etcd.store, "the winner's record was deleted by the loser's rollback"
        assert await superseded._subnet_allocator.holder(str(info.options["subnet"])) == "s1"
        assert await superseded._vni_allocator.holder(int(cast(int, info.options["vni"]))) == "s1"
        assert etcd.store["network/session/s1/endpoints/k1"]

    async def test_a_destroyed_session_cannot_be_resurrected(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        held = etcd.store[_META_KEY]  # what a create still running would be holding
        await plugin.destroy_network("s1")
        with pytest.raises(SessionRecordContested):
            await plugin._publish(
                cast(AsyncEtcd, etcd),
                "s1",
                held,
                {"subnet": info.options["subnet"], "_state": "ready"},
            )
        assert _META_KEY not in etcd.store, "a destroyed session was written back into etcd"

    async def test_only_one_of_two_waiters_takes_the_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gate = asyncio.Event()
        etcd = _GateOnGet(gate)
        etcd.store[_META_KEY] = json.dumps({"_owner": "tok-dead", "_state": "creating"})
        self._hand_over_at_once(monkeypatch)
        tasks = [
            asyncio.create_task(
                _plugin_with(etcd)._claim_session(cast(AsyncEtcd, etcd), "s1", f"tok{n}", [])
            )
            for n in range(2)
        ]
        await asyncio.sleep(0)  # both reach the read, and so both see the dead creator's record
        gate.set()
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        took = [outcome for outcome in outcomes if not isinstance(outcome, BaseException)]
        refused = [outcome for outcome in outcomes if isinstance(outcome, SessionRecordContested)]
        assert len(took) == 1, f"two waiters both believe they own the session: {outcomes}"
        assert len(refused) == 1, f"the loser was not told: {outcomes}"
        assert etcd.store[_META_KEY] == took[0][0]


class TestAMemberRecordTheAgentWrote:
    """The member record IS the teardown acknowledgement: the agent writes it with ``joined``
    once its devices, XFRM state and firewall rules are up, and `destroy_network` refuses to hand
    the VNI back while one stands. Anything of the manager's that overwrote it -- the pre-seed,
    which says only which nodes are *expected* -- put the VNI in the pool over live state."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "member_agents": ["a1"],
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    @staticmethod
    def _agent_joined(etcd: FakeEtcd) -> None:
        etcd.store["network/agent/a1/vtep"] = "10.0.0.1"
        etcd.store["network/session/s1/members/a1"] = json.dumps(
            Member(
                agent_id="a1", host_ip="10.0.0.1", vtep_ip="10.0.0.1", joined=True
            ).to_etcd_payload()
        )

    async def test_a_preseed_does_not_take_it_back(self) -> None:
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        plugin = _plugin_with(etcd)
        self._agent_joined(etcd)

        await plugin._preseed_members("s1", ["a1"])

        member = json.loads(etcd.store["network/session/s1/members/a1"])
        assert member["joined"] is True, "the pre-seed downgraded a node that had joined"

    async def test_the_vni_is_not_handed_back_over_a_joined_node(self) -> None:
        # The shape this comes in: a create that was taken over for being slow wakes up and
        # carries on through its own remaining steps, of which the pre-seed is one -- by then the
        # winner's session is running and its agents have published themselves.
        etcd = FakeEtcd()
        _encryption_capable(etcd, "a1")
        winner = _plugin_with(etcd)
        info = await winner.create_network(identifier="s1", options=dict(self._OPTIONS))
        self._agent_joined(etcd)

        await _plugin_with(etcd)._preseed_members("s1", ["a1"])

        with pytest.raises(OverlayTeardownPending):
            await winner.destroy_network("s1")
        assert await winner._vni_allocator.holder(int(cast(int, info.options["vni"]))) == "s1"


class TestARollbackThatCouldNotFinish:
    """C4b. The record is the only thing that names the session's subnet and VNI. A rollback that
    deleted it first and then failed left them allocated to a session no key mentions -- and
    `destroy_network`, which reads the meta to know what to give back, had nothing to read."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    class _RefusesSessionDeletes(FakeEtcd):
        """An etcd the cleanup cannot delete this session's keys through."""

        def __init__(self) -> None:
            super().__init__()
            self.refusing = True

        @override
        async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
            if self.refusing and key.startswith("network/session/"):
                raise RuntimeError("etcd is unreachable")
            return await super().delete_if_value(key, expected, **kwargs)

    async def _rolled_back(self) -> tuple[_RefusesSessionDeletes, CNINetworkPlugin, Any]:
        etcd = self._RefusesSessionDeletes()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        await plugin._rollback_create(
            "s1",
            str(info.options["subnet"]),
            int(cast(int, info.options["vni"])),
            etcd.store[_META_KEY],
        )
        return etcd, plugin, info

    async def test_the_record_stays_as_a_tombstone_naming_the_allocation(self) -> None:
        etcd, plugin, info = await self._rolled_back()
        meta = json.loads(etcd.store[_META_KEY])
        assert meta["_state"] == "deleting"
        assert meta["subnet"] == info.options["subnet"]
        assert meta["vni"] == info.options["vni"]
        assert await plugin._subnet_allocator.holder(str(info.options["subnet"])) == "s1"

    async def test_a_tombstone_is_not_handed_to_the_next_caller(self) -> None:
        etcd, plugin, _info = await self._rolled_back()
        assert await plugin._existing_allocation(cast(AsyncEtcd, etcd), "s1", []) is None

    async def test_destroy_finishes_from_it(self) -> None:
        etcd, plugin, _info = await self._rolled_back()
        etcd.refusing = False  # etcd is back

        await plugin.destroy_network("s1")

        assert _pool_claims(etcd) == [], "the subnet and VNI outlived the session"
        assert _META_KEY not in etcd.store


class TestATombstoneIsNotSomethingToBuildOn:
    """C4c. A cleanup that did not reach the end leaves a record naming a subnet and a VNI that
    are still allocated. A create must not take that over the way it takes over a stalled one:
    it would run the session on keys and an allocation something else is still deleting."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    class _RefusesSessionDeletes(FakeEtcd):
        """An etcd the cleanup cannot delete this session's keys through."""

        def __init__(self) -> None:
            super().__init__()
            self.refusing = True

        @override
        async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
            if self.refusing and key.startswith("network/session/"):
                raise RuntimeError("etcd is unreachable")
            return await super().delete_if_value(key, expected, **kwargs)

    async def _tombstoned(self) -> tuple[_RefusesSessionDeletes, CNINetworkPlugin]:
        etcd = self._RefusesSessionDeletes()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        await plugin._rollback_create(
            "s1",
            str(info.options["subnet"]),
            int(cast(int, info.options["vni"])),
            etcd.store[_META_KEY],
        )
        assert json.loads(etcd.store[_META_KEY])["_state"] == "deleting"
        return etcd, plugin

    async def test_a_create_finishes_the_cleanup_instead_of_taking_it_over(self) -> None:
        etcd, plugin = await self._tombstoned()
        etcd.refusing = False  # etcd is back by the time the next create arrives

        held, published = await plugin._claim_session(cast(AsyncEtcd, etcd), "s1", "tok2", [])

        assert published is None
        assert json.loads(held)["_state"] == "creating"
        assert _pool_claims(etcd) == [], "the tombstoned allocation was never given back"
        assert "network/session/s1/endpoints/k1" not in etcd.store

    async def test_a_create_refuses_while_the_cleanup_cannot_finish(self) -> None:
        etcd, plugin = await self._tombstoned()
        with pytest.raises(SessionCleanupPending):
            await plugin._claim_session(cast(AsyncEtcd, etcd), "s1", "tok2", [])
        assert json.loads(etcd.store[_META_KEY])["_state"] == "deleting"


class TestADestroyThatCrossesACreate:
    """C7. Destroy used to read the member table and the meta, then delete the prefix, all as
    separate steps. A create that had claimed a subnet but not yet published it lost the record
    its own rollback works from -- and what it held was then allocated to a session no key
    mentions."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    @staticmethod
    def _being_created(etcd: FakeEtcd, *, claimed_at: float) -> str:
        record = json.dumps({"_owner": "tok1", "_state": "creating", "_claimed_at": claimed_at})
        etcd.store[_META_KEY] = record
        return record

    async def test_it_waits_for_a_create_that_is_still_running(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        record = self._being_created(etcd, claimed_at=time.time())

        with pytest.raises(OverlayTeardownPending):
            await plugin.destroy_network("s1")

        assert etcd.store[_META_KEY] == record, "it deleted the record the create rolls back from"

    async def test_it_takes_over_a_create_nobody_is_coming_back_for(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        # What the dead create had claimed, and had not yet published.
        await plugin._subnet_allocator.acquire("s1")
        await plugin._vni_allocator.acquire("s1")
        self._being_created(etcd, claimed_at=time.time() - 3600)

        await plugin.destroy_network("s1")

        assert _pool_claims(etcd) == [], "the dead create's claims outlived its session"
        assert _META_KEY not in etcd.store

    async def test_a_create_that_was_overtaken_cannot_publish_afterwards(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        held = self._being_created(etcd, claimed_at=time.time() - 3600)
        await plugin.destroy_network("s1")
        with pytest.raises(SessionRecordContested):
            await plugin._publish(cast(AsyncEtcd, etcd), "s1", held, {"subnet": "10.128.0.0/24"})


class TestACleanupThatComesBackTooLate:
    """C4d. A cleanup can be paused between its steps -- a slow etcd, a manager that swapped out.
    By the time it resumes, another cleanup may have finished the job and a new session may hold
    the same id. Its endpoint keys, its member keys and its pool claim all name the SESSION, not
    the attempt that made them (`ipam._claim`), so nothing but the tombstone tells the new
    session's state apart from the state this cleanup came to delete."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    async def _cleaned_up_then_rebuilt(self) -> tuple[FakeEtcd, CNINetworkPlugin, str]:
        """A session cleaned up under one tombstone and built again under the same id.

        Returns the tombstone the first cleanup was working from -- the one a late resumer still
        holds in its own stack.
        """
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        stale = cni._tombstone(
            "10.128.0.0/24", 4096, "tok1", json.loads(etcd.store[_META_KEY])["generation"]
        )
        etcd.store[_META_KEY] = stale
        assert await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", stale)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        return etcd, plugin, stale

    async def test_it_stops_instead_of_finishing(self) -> None:
        etcd, plugin, stale = await self._cleaned_up_then_rebuilt()
        assert not await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", stale)

    async def test_the_new_sessions_allocation_is_left_alone(self) -> None:
        etcd, plugin, stale = await self._cleaned_up_then_rebuilt()
        meta = json.loads(etcd.store[_META_KEY])

        await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", stale)

        assert await plugin._subnet_allocator.holder(str(meta["subnet"])) == "s1"
        assert await plugin._vni_allocator.holder(int(meta["vni"])) == "s1"

    async def test_the_new_sessions_keys_are_left_alone(self) -> None:
        etcd, plugin, stale = await self._cleaned_up_then_rebuilt()

        await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", stale)

        assert "network/session/s1/endpoints/k1" in etcd.store
        assert etcd.store[_META_KEY] != stale, "it deleted the new session's record"

    async def test_two_cleanups_cannot_hold_one_tombstone(self) -> None:
        # The take, not just the check: two managers reading one DELETING record must not both
        # come away working from those same bytes.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        first = cni._tombstone(
            "10.128.0.0/24", 4096, "tok1", json.loads(etcd.store[_META_KEY])["generation"]
        )
        etcd.store[_META_KEY] = first

        held, published = await plugin._claim_session(cast(AsyncEtcd, etcd), "s1", "tok2", [])

        assert published is None
        assert json.loads(held)["_state"] == "creating"
        # The cleanup ran from bytes only it held, not from the record both managers had read.
        assert not await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", first)


class TestACleanupPausedBetweenItsCheckAndItsDelete:
    """C4e. Holding the tombstone is a check followed by a separate delete, and the gap between
    them is a window: another manager can take the record, finish the cleanup and let a whole new
    session be built under the same id while this call sits between its own two lines. Everything
    the new session writes is named after the SESSION, so by key alone it is indistinguishable from
    what this cleanup came to delete -- only the generation tells them apart."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    class _RebuildsAfterTheCheck(FakeEtcd):
        """Runs a hook the first time the meta is read, AFTER handing back what was there.

        That is exactly where a cleanup's tombstone check sits: it reads the record, is satisfied,
        and the world moves on before its next line executes.
        """

        def __init__(self) -> None:
            super().__init__()
            self.after_meta_read: Any = None

        @override
        async def get(self, key: str, **kwargs: Any) -> str | None:
            found = await super().get(key, **kwargs)
            if key == _META_KEY and self.after_meta_read is not None:
                hook, self.after_meta_read = self.after_meta_read, None
                await hook()
            return found

    async def _paused_cleanup(self) -> tuple[_RebuildsAfterTheCheck, CNINetworkPlugin, str]:
        """A cleanup working from a tombstone whose session is rebuilt the moment it looks away."""
        etcd = self._RebuildsAfterTheCheck()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        record = json.loads(etcd.store[_META_KEY])
        stale = cni._tombstone(
            str(record["subnet"]), record["vni"], record["_owner"], record["generation"]
        )
        etcd.store[_META_KEY] = stale

        async def rebuild() -> None:
            # Another manager finishes this very cleanup and builds the session again.
            assert await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", stale)
            await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        etcd.after_meta_read = rebuild
        return etcd, plugin, stale

    async def test_the_new_sessions_pool_claim_is_not_given_back(self) -> None:
        etcd, plugin, stale = await self._paused_cleanup()

        await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", stale)

        rebuilt = json.loads(etcd.store[_META_KEY])
        assert await plugin._subnet_allocator.holder(str(rebuilt["subnet"])) == "s1"
        assert await plugin._vni_allocator.holder(int(rebuilt["vni"])) == "s1"

    async def test_the_new_sessions_keys_are_not_deleted(self) -> None:
        etcd, plugin, stale = await self._paused_cleanup()

        await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", stale)

        assert "network/session/s1/endpoints/k1" in etcd.store
        assert [key for key in etcd.store if key.startswith("network/session/s1/ipam/")]

    async def test_the_new_sessions_record_survives(self) -> None:
        etcd, plugin, stale = await self._paused_cleanup()

        await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", stale)

        assert json.loads(etcd.store[_META_KEY])["_state"] == "ready"

    async def test_it_still_clears_its_own_incarnation(self) -> None:
        # The fence must not turn the cleanup into a no-op: with nobody rebuilding underneath it,
        # everything the tombstone's incarnation owns still goes.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        record = json.loads(etcd.store[_META_KEY])
        tombstone = cni._tombstone(
            str(record["subnet"]), record["vni"], record["_owner"], record["generation"]
        )
        etcd.store[_META_KEY] = tombstone

        assert await plugin._finish_cleanup(cast(AsyncEtcd, etcd), "s1", tombstone)

        assert _pool_claims(etcd) == []
        assert not [key for key in etcd.store if key.startswith("network/session/s1/")]


class TestAnAllocationReusedWhileItIsBeingDestroyed:
    """C4f. A retried create that finds a READY record checks the pool still calls the allocation
    this session's, then writes the endpoints and hands it back. A destroy can run in between: it
    fences the record and gives the subnet and the VNI to the pool, and what the retry returns is
    then an allocation somebody else is about to be handed."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    class _DestroysDuringTheAssign(FakeEtcd):
        """Tears the session down inside the endpoint assignment -- after the pool has been asked
        whether the allocation is still this session's, and before the caller is handed it."""

        def __init__(self) -> None:
            super().__init__()
            self.at_assign: Any = None

        @override
        async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
            found = await super().get_prefix(prefix, **kwargs)
            if prefix.rstrip("/").endswith("/ipam") and self.at_assign is not None:
                hook, self.at_assign = self.at_assign, None
                await hook()
            return found

    async def test_it_does_not_hand_back_an_allocation_that_went_back_to_the_pool(self) -> None:
        etcd = self._DestroysDuringTheAssign()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        async def destroy() -> None:
            await plugin.destroy_network("s1")

        etcd.at_assign = destroy

        assert (
            await plugin._existing_allocation(
                cast(AsyncEtcd, etcd), "s1", list(self._OPTIONS["endpoints"])
            )
            is None
        )
        assert _pool_claims(etcd) == []


class TestANodeThatJoinsAsTheRecordIsFenced:
    """C9. The manager decides a session's nodes have let go by reading the membership table, and
    a node publishes its membership before it builds anything. One read, taken before the record
    was fenced, could see neither: the node publishes after it, the fence lands after that, and the
    node goes on to build a tunnel on a VNI already back in the pool."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    class _AgentJoinsAfterTheFirstRead(FakeEtcd):
        """A node whose member key lands after the teardown's first membership read."""

        def __init__(self) -> None:
            super().__init__()
            self.member: str | None = None

        @override
        async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
            found = await super().get_prefix(prefix, **kwargs)
            if prefix.rstrip("/").endswith("/members") and self.member is not None:
                self.store["network/session/s1/members/a1"] = self.member
                self.member = None
            return found

    async def test_the_teardown_refuses_rather_than_reusing_the_vni(self) -> None:
        etcd = self._AgentJoinsAfterTheFirstRead()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        etcd.member = json.dumps(
            Member(
                agent_id="a1",
                host_ip="10.0.0.1",
                vtep_ip="10.0.0.1",
                joined=True,
                generation=str(info.options["generation"]),
            ).to_etcd_payload()
        )

        with pytest.raises(OverlayTeardownPending):
            await plugin.destroy_network("s1")

        assert await plugin._vni_allocator.holder(int(cast(int, info.options["vni"]))) == "s1"
        assert await plugin._subnet_allocator.holder(str(info.options["subnet"])) == "s1"


class TestACreateThatWokeUpInAnotherSession:
    """C14. A create stalled past the handover holds the old subnet, the old VNI and the old
    generation. If its session was torn down and built again while it slept, everything it goes on
    to write lands in the LIVE session's table -- and its own rollback, finding the record is not
    its, used to clean up nothing at all."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    async def _stalled_create(self) -> tuple[FakeEtcd, CNINetworkPlugin, str, str]:
        """A rebuilt session, plus the record bytes a create of the previous one still holds."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        first = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        held = etcd.store[_META_KEY]
        await plugin.destroy_network("s1")
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        return etcd, plugin, held, str(first.options["subnet"])

    async def test_its_endpoint_write_is_refused(self) -> None:
        etcd, plugin, held, stale_subnet = await self._stalled_create()
        live = json.loads(etcd.store["network/session/s1/endpoints/k1"])

        with pytest.raises(EndpointSuperseded):
            await plugin._endpoint_allocator.assign(
                "s1",
                "k1",
                stale_subnet,
                agent_id="a1",
                generation=json.loads(held)["generation"],
            )

        assert json.loads(etcd.store["network/session/s1/endpoints/k1"]) == live, (
            "the live session's peers were pointed at an address nothing holds"
        )

    async def test_its_rollback_gives_back_what_it_still_holds(self) -> None:
        etcd, plugin, held, _stale_subnet = await self._stalled_create()
        stale_generation = json.loads(held)["generation"]
        # What that create claimed before it stalled, still stamped with its own incarnation.
        etcd.store["network/ipam/vni/9999"] = json.dumps({
            "session_id": "s1",
            "generation": stale_generation,
        })
        etcd.store["network/session/s1/ipam/10.99.99.1"] = json.dumps({
            "container_id": "k1",
            "generation": stale_generation,
        })
        live_meta = etcd.store[_META_KEY]

        await plugin._rollback_create("s1", None, None, held)

        assert "network/ipam/vni/9999" not in etcd.store
        assert "network/session/s1/ipam/10.99.99.1" not in etcd.store
        assert etcd.store[_META_KEY] == live_meta, "it wrote over the live session's record"

    async def test_it_leaves_the_live_incarnation_alone(self) -> None:
        etcd, plugin, held, _stale_subnet = await self._stalled_create()
        live = json.loads(etcd.store[_META_KEY])

        await plugin._rollback_create("s1", None, None, held)

        assert await plugin._subnet_allocator.holder(str(live["subnet"])) == "s1"
        assert await plugin._vni_allocator.holder(int(live["vni"])) == "s1"
        assert "network/session/s1/endpoints/k1" in etcd.store

    async def test_a_takeover_is_not_a_rollback(self) -> None:
        # The same record bytes, but the session was TAKEN OVER rather than rebuilt: the new owner
        # inherited this very incarnation, and everything claimed for it is still the session's.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        held = etcd.store[_META_KEY]
        taken = json.loads(held)
        taken["_owner"] = "another-manager"
        etcd.store[_META_KEY] = json.dumps(taken)

        await plugin._rollback_create("s1", str(info.options["subnet"]), None, held)

        assert await plugin._subnet_allocator.holder(str(info.options["subnet"])) == "s1"
        assert "network/session/s1/endpoints/k1" in etcd.store


class TestASubnetTwoIncarnationsBothClaim:
    """C15. Ownership of a pool claim is (session, incarnation), not the session id. A stalled
    create's block adopted by the incarnation that replaced it is a block the stalled one's cleanup
    still gives back -- and the pool then hands it to a third session while the live one is on it.
    Two tenants at the same addresses, which is not a leak."""

    async def test_a_later_incarnation_does_not_adopt_an_earlier_ones_block(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        stranded = await plugin._subnet_allocator.acquire("s1", generation="g1")

        mine = await plugin._subnet_allocator.acquire("s1", generation="g2")

        assert mine != stranded, "g2 took over a block g1's cleanup will give back"
        assert await plugin._subnet_allocator.holder(stranded) == "s1"

    async def test_the_earlier_incarnations_release_leaves_the_later_one_alone(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin._subnet_allocator.acquire("s1", generation="g1")
        live = await plugin._subnet_allocator.acquire("s1", generation="g2")

        await plugin._subnet_allocator.release_all("s1", "g1")

        assert await plugin._subnet_allocator.holder(live) == "s1"

    async def test_a_retry_of_the_same_incarnation_still_converges(self) -> None:
        # The idempotency this ownership rule must not cost: a retried create of ONE incarnation
        # lands on the block it already holds rather than claiming a second.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        first = await plugin._subnet_allocator.acquire("s1", generation="g1")

        assert await plugin._subnet_allocator.acquire("s1", generation="g1") == first
        assert len(_pool_claims(etcd)) == 1

    async def test_a_claim_from_before_the_field_is_still_adopted(self) -> None:
        # A manager older than the generation wrote no stamp, and nothing else will come back for
        # what it left; refusing to adopt it would strand the block for the cluster's lifetime.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        legacy = await plugin._subnet_allocator.acquire("s1")

        assert await plugin._subnet_allocator.acquire("s1", generation="g1") == legacy

    async def test_the_same_holds_for_a_vni(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        stranded = await plugin._vni_allocator.acquire("s1", "g1")

        mine = await plugin._vni_allocator.acquire("s1", "g2")

        assert mine != stranded
        assert await plugin._vni_allocator.holder(stranded) == "s1"


class TestAChildKeyWrittenUnderNoRecord:
    """C16. A stamp says whose a key is; it cannot stop the key being MADE. A stale create finding
    an address free is finding it free because the session it belonged to was torn down, and the
    endpoint or member key it then creates is attached to a session that no longer exists -- where
    it blocks the teardown of whatever replaces it and nothing ever comes for it. So each write is
    one store operation with the check that this create still holds the session's record."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    async def test_an_endpoint_is_not_created_under_a_record_that_moved_on(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        held = etcd.store[_META_KEY]
        await plugin.destroy_network("s1")
        assert _META_KEY not in etcd.store

        with pytest.raises(EndpointSuperseded):
            await plugin._endpoint_allocator.assign(
                "s1",
                "k1",
                "10.128.0.0/24",
                agent_id="a1",
                generation=json.loads(held)["generation"],
                guards={_META_KEY: held},
            )

        assert "network/session/s1/endpoints/k1" not in etcd.store
        assert not [key for key in etcd.store if key.startswith("network/session/s1/ipam/")]

    async def test_a_preseeded_member_is_not_created_under_one_either(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        etcd.store["network/agent/a1/vtep"] = "192.168.105.7"

        await plugin._preseed_members("s1", ["a1"], "g1", held='{"gone": true}')

        assert member_key("s1", "a1") not in etcd.store, (
            "it put a member under a session whose record it does not hold; that key is what"
            " holds a VNI back from reuse, and nothing would come for it"
        )

    async def test_the_guarded_write_still_lands_under_the_record_it_names(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        assert "network/session/s1/endpoints/k1" in etcd.store
        assert info.options["endpoint_ips"] == {"k1": "10.128.0.1"}


class TestACleanupThatCouldNotFinishIsRetried:
    """C17. The orphan sweep has no tombstone to work from -- the record already names the
    incarnation that replaced the one being given back -- so a failure there is a leak nothing
    else can find. It writes down what it owes, and the next use of the session id pays it."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    class _PoolIsUnreachable(FakeEtcd):
        def __init__(self) -> None:
            super().__init__()
            self.refusing = True

        @override
        async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
            if self.refusing and key.startswith("network/ipam/"):
                raise RuntimeError("etcd is unreachable")
            return await super().delete_if_value(key, expected, **kwargs)

    async def test_a_failed_sweep_is_written_down(self) -> None:
        etcd = self._PoolIsUnreachable()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        held = etcd.store[_META_KEY]
        generation = json.loads(held)["generation"]
        etcd.store[_META_KEY] = _rebuilt_as("later")

        await plugin._rollback_create("s1", None, None, held)

        assert f"network/cleanup-debt/s1/{generation}" in etcd.store

    async def test_the_next_use_of_the_id_pays_it(self) -> None:
        etcd = self._PoolIsUnreachable()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        held = etcd.store[_META_KEY]
        generation = json.loads(held)["generation"]
        # The session is rebuilt, so the sweep has no record of its own to hang off.
        etcd.store[_META_KEY] = _rebuilt_as("later")
        await plugin._rollback_create("s1", None, None, held)
        assert _pool_claims(etcd) != [], "nothing was owed"
        etcd.refusing = False  # etcd is back

        await plugin.drain_cleanup_debt("s1")

        assert _pool_claims(etcd) == [], "the leak outlived the session"
        assert f"network/cleanup-debt/s1/{generation}" not in etcd.store

    async def test_a_sweep_that_finishes_owes_nothing(self) -> None:
        etcd = self._PoolIsUnreachable()
        etcd.refusing = False
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        held = etcd.store[_META_KEY]
        generation = json.loads(held)["generation"]
        etcd.store[_META_KEY] = json.dumps({**json.loads(held), "generation": "later"})

        await plugin._rollback_create("s1", None, None, held)

        assert f"network/cleanup-debt/s1/{generation}" not in etcd.store


class _RecordsGuards(FakeEtcd):
    """Remembers what each write was conditional on, so a missing guard is visible."""

    def __init__(self) -> None:
        super().__init__()
        self.guarded: dict[str, dict[str, str]] = {}

    @override
    async def compare_and_put(
        self,
        key: str,
        val: str,
        *,
        expected: str | None,
        guards: Mapping[str, str],
        **kwargs: Any,
    ) -> bool:
        written = await super().compare_and_put(
            key, val, expected=expected, guards=guards, **kwargs
        )
        if written:
            self.guarded[key] = dict(guards)
        return written


class TestTheGuardIsWiredIntoTheRealPath:
    """C18. A guard that exists on the allocator and is not passed by `create_network` protects
    nothing. Asserted through the PUBLIC entry points -- create, reuse, teardown -- and never by
    handing the allocator a guard the test made up, because that is exactly the mistake this
    catches: `TestAChildKeyWrittenUnderNoRecord` passed while every real call site was unguarded.
    """

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
        "member_agents": ["a1"],
    }

    async def test_create_guards_every_key_it_writes_on_the_session_record(self) -> None:
        etcd = _RecordsGuards()
        etcd.store["network/agent/a1/vtep"] = "192.168.105.7"
        _encryption_capable(etcd, "a1")
        plugin = _plugin_with(etcd)

        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        written = {
            key: guards for key, guards in etcd.guarded.items() if key.startswith("network/")
        }
        unguarded = [key for key, guards in written.items() if _META_KEY not in guards]
        assert written, "nothing went through the guarded write at all"
        assert not unguarded, (
            f"these keys were written without naming the session record: {sorted(unguarded)}"
        )

    async def test_the_pool_claims_are_guarded_too(self) -> None:
        etcd = _RecordsGuards()
        plugin = _plugin_with(etcd)

        await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})

        pool = [key for key in etcd.guarded if key.startswith("network/ipam/")]
        assert pool, "no pool claim went through the guarded write"
        for key in pool:
            assert _META_KEY in etcd.guarded[key], f"{key} was claimed under no record"

    async def test_a_create_whose_record_is_taken_writes_nothing_further(self) -> None:
        """The guard's actual job, through the real path: the record is replaced mid-create, and
        the endpoint keys that follow must not be written under it."""

        class _TakenMidCreate(_RecordsGuards):
            """Takes the session over at the address assignment.

            The create reads this session's ipam prefix twice: once on the way in, where it
            reconciles anything an earlier incarnation of the id left, and once inside the
            assignment. It is the second that this test is about, so the first is let through.
            """

            def __init__(self) -> None:
                super().__init__()
                self.armed = False
                self.ipam_reads = 0

            @override
            async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
                found: dict[str, str] = await super().get_prefix(prefix, **kwargs)
                if prefix.rstrip("/").endswith("/ipam"):
                    self.ipam_reads += 1
                if self.armed and self.ipam_reads > 1 and prefix.rstrip("/").endswith("/ipam"):
                    self.armed = False
                    # Somebody else takes the session while this create is assigning addresses.
                    self.store[_META_KEY] = json.dumps({
                        "_owner": "someone-else",
                        "_state": "ready",
                    })
                return found

        etcd = _TakenMidCreate()
        _encryption_capable(etcd, "a1")
        plugin = _plugin_with(etcd)
        etcd.armed = True

        with pytest.raises(EndpointSuperseded):
            await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        assert "network/session/s1/endpoints/k1" not in etcd.store, (
            "it wrote an endpoint under a record it no longer held"
        )

    async def test_the_preseeded_member_names_the_record(self) -> None:
        etcd = _RecordsGuards()
        etcd.store["network/agent/a1/vtep"] = "192.168.105.7"
        _encryption_capable(etcd, "a1")
        plugin = _plugin_with(etcd)

        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        assert _META_KEY in etcd.guarded[member_key("s1", "a1")]


class TestAGuardThatExpiredMidScan:
    """C19. A lost compare-and-swap has two causes that mean opposite things: the candidate was
    taken, or the session's record moved on. Read as the first, an expired guard makes every
    candidate lose in turn -- 16 million VNIs, each costing a swap and a prefix read -- and one
    stale create holds the manager and its etcd for as long as that takes."""

    async def test_a_vni_scan_stops_instead_of_walking_the_pool(self) -> None:
        etcd = FakeEtcd()
        etcd.store[_META_KEY] = "the record this create holds"
        allocator = _vni_allocator(etcd, vni_range=(4096, 16_777_215))
        # The record moves on before the claim is attempted, so every swap will lose.
        etcd.store[_META_KEY] = "somebody else's now"

        with pytest.raises(SessionRecordContested):
            await allocator.acquire("s1", "g1", {_META_KEY: "the record this create holds"})

    async def test_it_costs_one_attempt_not_the_whole_range(self) -> None:
        etcd = _CountingCas()
        etcd.store[_META_KEY] = "moved on"
        allocator = _vni_allocator(etcd, vni_range=(4096, 16_777_215))

        with pytest.raises(SessionRecordContested):
            await allocator.acquire("s1", "g1", {_META_KEY: "held"})

        assert etcd.cas <= 2, f"it tried {etcd.cas} candidates on a record it no longer held"

    async def test_a_subnet_scan_stops_too(self) -> None:
        etcd = FakeEtcd()
        etcd.store[_META_KEY] = "moved on"
        allocator = _subnet_allocator(etcd)

        with pytest.raises(SessionRecordContested):
            await allocator.acquire("s1", generation="g1", guards={_META_KEY: "held"})

    async def test_a_live_guard_still_skips_a_taken_candidate(self) -> None:
        # The fence must not turn an ordinary conflict into a failure.
        etcd = FakeEtcd()
        etcd.store[_META_KEY] = "held"
        allocator = _vni_allocator(etcd, vni_range=(4096, 4098))
        etcd.store["network/ipam/vni/4096"] = json.dumps({"session_id": "other"})

        got = await allocator.acquire("s1", "g1", {_META_KEY: "held"})

        assert got == 4097


class TestALegacyClaimTwoIncarnationsCanRead:
    """C20. A claim from before the incarnation field answers to whoever asks (`of_generation`).
    That is right for finding it and wrong for keeping it: a new incarnation starts using the VNI,
    a delayed cleanup of the old one reads the same claim as its own and gives the VNI back, and
    the pool hands a running session's VNI to the next."""

    async def test_a_legacy_vni_is_promoted_before_it_is_used(self) -> None:
        etcd = FakeEtcd()
        etcd.store[_META_KEY] = "held"
        allocator = _vni_allocator(etcd, vni_range=(4096, 4100))
        etcd.store["network/ipam/vni/4096"] = json.dumps({"session_id": "s1"})

        got = await allocator.acquire("s1", "g2", {_META_KEY: "held"})

        assert got == 4096
        assert json.loads(etcd.store["network/ipam/vni/4096"])["generation"] == "g2", (
            "the claim still answers to any incarnation that asks"
        )

    async def test_the_old_incarnations_cleanup_no_longer_takes_it(self) -> None:
        etcd = FakeEtcd()
        etcd.store[_META_KEY] = "held"
        allocator = _vni_allocator(etcd, vni_range=(4096, 4100))
        etcd.store["network/ipam/vni/4096"] = json.dumps({"session_id": "s1"})
        got = await allocator.acquire("s1", "g2", {_META_KEY: "held"})

        await allocator.release_all("s1", "g1")

        assert await allocator.holder(got) == "s1", "a stale cleanup took a running session's vni"

    async def test_a_promotion_that_cannot_land_does_not_hand_the_claim_back(self) -> None:
        # The guard is gone, so the promotion must not land -- and an unpromoted legacy claim
        # must not be returned as this incarnation's.
        etcd = FakeEtcd()
        allocator = _vni_allocator(etcd, vni_range=(4096, 4100))
        etcd.store["network/ipam/vni/4096"] = json.dumps({"session_id": "s1"})

        with pytest.raises(SessionRecordContested):
            await allocator.acquire("s1", "g2", {_META_KEY: "held"})

        assert "generation" not in json.loads(etcd.store["network/ipam/vni/4096"])


class TestAWideBlockOnTwoIncarnations:
    """C21. A block promoted unit by unit can end up half on one incarnation and half on another.
    An old cleanup then takes the legacy half while the session runs on the whole block, and the
    pool hands that half to a tenant whose addresses overlap it."""

    async def test_a_promotion_that_fails_partway_leaves_the_block_as_it_was(self) -> None:
        class _RefusesTheSecondUnit(FakeEtcd):
            def __init__(self) -> None:
                super().__init__()
                self.seen = 0

            @override
            async def compare_and_put(self, key: str, val: str, **kwargs: Any) -> bool:
                if key.startswith("network/ipam/allocated/"):
                    self.seen += 1
                    if self.seen == 2:
                        return False
                return await super().compare_and_put(key, val, **kwargs)

        etcd = _RefusesTheSecondUnit()
        allocator = _subnet_allocator(etcd)
        for unit in ("10.128.0.0/24", "10.128.1.0/24"):
            etcd.store[_allocated_key(unit)] = _claim("s1", "10.128.0.0/23")

        assert not await allocator._claim_as_ours(
            _flat_claims(etcd), "10.128.0.0/23", "s1", "g1", {}
        )

        stamped = [
            json.loads(etcd.store[_allocated_key(u)]).get("generation")
            for u in ("10.128.0.0/24", "10.128.1.0/24")
        ]
        assert stamped == [None, None], f"the block was left on two incarnations: {stamped}"

    async def test_a_completed_partial_claim_ends_on_one_incarnation(self) -> None:
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        # Half of a /23 claimed before the incarnation field existed.
        etcd.store[_allocated_key("10.128.0.0/24")] = _claim("s1", "10.128.0.0/23")

        got = await allocator.acquire("s1", host_count=400, generation="g1")

        assert got == "10.128.0.0/23"
        stamped = {
            json.loads(etcd.store[_allocated_key(u)]).get("generation")
            for u in ("10.128.0.0/24", "10.128.1.0/24")
        }
        assert stamped == {"g1"}, f"the block answers to more than one incarnation: {stamped}"


class TestAPoolClaimNothingNames:
    """C22. A sweep whose debt note could not be written AND whose release failed leaves a subnet
    and a VNI that no record, tombstone or debt key mentions. The pool is then the only evidence
    they exist, so the reconciler starts there and asks the session -- not from a list of what is
    owed, which is exactly what was lost."""

    _OPTIONS = {"forced_backend": "vxlan"}

    async def test_a_claim_whose_session_is_gone_is_reclaimed(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        del etcd.store[_META_KEY]  # the record went; the claims did not

        assert await plugin.reconcile_pool() > 0
        assert _pool_claims(etcd) == []

    async def test_a_claim_of_a_superseded_incarnation_is_reclaimed(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        etcd.store[_META_KEY] = _rebuilt_as("later")

        await plugin.reconcile_pool()

        assert _pool_claims(etcd) == []

    async def test_a_live_sessions_claims_are_left_alone(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        assert await plugin.reconcile_pool() == 0

        assert await plugin._subnet_allocator.holder(str(info.options["subnet"])) == "s1"
        assert await plugin._vni_allocator.holder(int(cast(int, info.options["vni"]))) == "s1"

    async def test_a_create_still_building_keeps_its_claims(self) -> None:
        # Its record is CREATING, not READY -- and that record is what says the claims are its.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        held, _ = await plugin._claim_session(cast(AsyncEtcd, etcd), "s1", "tok", [])
        generation = json.loads(held)["generation"]
        await plugin._subnet_allocator.acquire("s1", generation=generation)

        assert await plugin.reconcile_pool() == 0
        assert _pool_claims(etcd) != []

    async def test_a_claim_retaken_between_the_judgement_and_the_delete_survives(self) -> None:
        """The race the static cases cannot show. The sweep decides a claim is an orphan by
        reading a session record; between that read and the delete the record can appear and the
        claim be released and taken by the very session it now names. A delete conditioned on what
        is there NOW rather than on what was judged takes a live tenant's subnet."""

        class _ReallocatesAfterTheJudgement(FakeEtcd):
            """Rebuilds the session -- with the same unit block -- the moment the sweep reads its
            record and finds none."""

            def __init__(self) -> None:
                super().__init__()
                self.armed = False
                self.rebuild: Any = None

            @override
            async def get(self, key: str, **kwargs: Any) -> str | None:
                found = await super().get(key, **kwargs)
                if self.armed and key == _META_KEY and found is None:
                    self.armed = False
                    hook, self.rebuild = self.rebuild, None
                    if hook is not None:
                        await hook()
                return found

        etcd = _ReallocatesAfterTheJudgement()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        first = dict(_flat_claims(etcd))
        # The session's record is gone and its claims are not: the shape the sweep is for.
        del etcd.store[_META_KEY]

        async def rebuild() -> None:
            # ... but s1 comes back, over the very same units, while the sweep is deciding.
            for unit_key in first:
                etcd.store[f"network/ipam/allocated/{unit_key}"] = json.dumps({
                    "session_id": "s1",
                    "subnet": json.loads(first[unit_key])["subnet"],
                    "generation": "g-new",
                })
            etcd.store[_META_KEY] = json.dumps({
                "_state": "ready",
                "generation": "g-new",
                "subnet": json.loads(next(iter(first.values())))["subnet"],
            })

        etcd.rebuild = rebuild
        etcd.armed = True

        await plugin.reconcile_pool()

        surviving = _flat_claims(etcd)
        assert surviving, "it deleted the claims of the session that had just been rebuilt"
        assert all(json.loads(raw)["generation"] == "g-new" for raw in surviving.values()), (
            f"a live claim was taken: {surviving}"
        )

    async def test_a_stale_session_key_is_reclaimed_too(self) -> None:
        # The pool is not the whole of what a failed sweep leaves: a member key that outlives its
        # incarnation holds the session's VNI back from reuse for a node that is not in it.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        record = json.loads(etcd.store[_META_KEY])
        etcd.store[member_key("s1", "a9")] = json.dumps(
            Member(
                agent_id="a9", host_ip="10.0.0.9", vtep_ip="10.0.0.9", joined=True, generation="old"
            ).to_etcd_payload()
        )
        etcd.store[_META_KEY] = json.dumps(record)  # the live record still names its own

        await plugin.reconcile_pool()

        assert member_key("s1", "a9") not in etcd.store
        assert _META_KEY in etcd.store, "it took the live session's record"

    async def test_a_live_sessions_legacy_subnet_survives_the_sweep(self) -> None:
        """The upgrade path, and the reason this is not hypothetical: the version before last
        could hand back an unstamped subnet claim to a session whose meta DOES carry a
        generation. Those sessions are running when the manager that upgraded them starts, and
        the sweep runs at that start."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        subnet = str(info.options["subnet"])
        # Its claim carries no incarnation, as one written before the field does.
        for unit_key in list(_flat_claims(etcd)):
            etcd.store[f"network/ipam/allocated/{unit_key}"] = json.dumps({
                "session_id": "s1",
                "subnet": subnet,
            })

        assert await plugin.reconcile_pool() == 0

        assert await plugin._subnet_allocator.holder(subnet) == "s1", (
            "it took a running session's subnet because the claim predates the field"
        )

    async def test_a_live_sessions_legacy_vni_survives_too(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        vni = int(cast(int, info.options["vni"]))
        etcd.store[f"network/ipam/vni/{vni}"] = json.dumps({"session_id": "s1"})

        await plugin.reconcile_pool()

        assert await plugin._vni_allocator.holder(vni) == "s1"

    async def test_the_allocator_still_promotes_it_afterwards(self) -> None:
        # Preserved, then taken: the sweep leaves it, and the next adoption stamps it.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        vni = int(cast(int, info.options["vni"]))
        generation = str(info.options["generation"])
        etcd.store[f"network/ipam/vni/{vni}"] = json.dumps({"session_id": "s1"})
        await plugin.reconcile_pool()

        again = await plugin._vni_allocator.acquire("s1", generation)

        assert again == vni
        assert json.loads(etcd.store[f"network/ipam/vni/{vni}"])["generation"] == generation

    async def test_the_sweep_takes_a_preserved_legacy_claim_rather_than_leaving_it(self) -> None:
        """Preserving is not enough. An unstamped claim is compatible with EVERY incarnation, so
        while it stays unstamped a cleanup for any earlier one takes it -- the session is running
        and its subnet goes back to the pool. The sweep has to stamp it, not just skip it."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        generation = str(info.options["generation"])
        subnet = str(info.options["subnet"])
        vni = int(cast(int, info.options["vni"]))
        for unit_key in list(_flat_claims(etcd)):
            etcd.store[f"network/ipam/allocated/{unit_key}"] = json.dumps({
                "session_id": "s1",
                "subnet": subnet,
            })
        etcd.store[f"network/ipam/vni/{vni}"] = json.dumps({"session_id": "s1"})

        await plugin.reconcile_pool()

        assert all(
            json.loads(raw).get("generation") == generation for raw in _flat_claims(etcd).values()
        ), "the subnet was left unstamped and any earlier cleanup can still take it"
        assert json.loads(etcd.store[f"network/ipam/vni/{vni}"])["generation"] == generation

    async def test_the_reuse_path_takes_it_too(self) -> None:
        # Through create_network, not through the allocator: the reuse path is what a running
        # session actually goes through, and it is where the previous round's test did not look.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        generation = str(info.options["generation"])
        vni = int(cast(int, info.options["vni"]))
        etcd.store[f"network/ipam/vni/{vni}"] = json.dumps({"session_id": "s1"})
        for unit_key in list(_flat_claims(etcd)):
            etcd.store[f"network/ipam/allocated/{unit_key}"] = json.dumps({
                "session_id": "s1",
                "subnet": str(info.options["subnet"]),
            })

        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        assert json.loads(etcd.store[f"network/ipam/vni/{vni}"])["generation"] == generation
        assert all(
            json.loads(raw).get("generation") == generation for raw in _flat_claims(etcd).values()
        )

    async def test_an_earlier_cleanup_does_not_take_a_live_unstamped_claim(self) -> None:
        """The window itself, closed from the other side. Even while a claim is still unstamped,
        a cleanup for an incarnation the record has moved on from must not take it."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        subnet = str(info.options["subnet"])
        vni = int(cast(int, info.options["vni"]))
        for unit_key in list(_flat_claims(etcd)):
            etcd.store[f"network/ipam/allocated/{unit_key}"] = json.dumps({
                "session_id": "s1",
                "subnet": subnet,
            })
        etcd.store[f"network/ipam/vni/{vni}"] = json.dumps({"session_id": "s1"})

        # A cleanup for an earlier incarnation of this same id.
        await plugin._sweep_incarnation(cast(AsyncEtcd, etcd), "s1", "g-earlier")

        assert await plugin._subnet_allocator.holder(subnet) == "s1", (
            "an earlier incarnation's cleanup took the live session's subnet"
        )
        assert await plugin._vni_allocator.holder(vni) == "s1"

    async def test_the_session_own_cleanup_still_takes_its_unstamped_claim(self) -> None:
        # The fence must not strand it: the tombstone IS the live record, so the claim is its.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        for unit_key in list(_flat_claims(etcd)):
            etcd.store[f"network/ipam/allocated/{unit_key}"] = json.dumps({
                "session_id": "s1",
                "subnet": str(info.options["subnet"]),
            })
        etcd.store[f"network/ipam/vni/{int(cast(int, info.options['vni']))}"] = json.dumps({
            "session_id": "s1"
        })

        await plugin.destroy_network("s1")

        assert _pool_claims(etcd) == [], "the session's own teardown could not give its pool back"

    async def test_promotion_does_not_take_a_block_another_session_now_holds(self) -> None:
        """The race the promotion opened. A promotion driven from a RECORD has no claim in front
        of it: between the record being read and the promotion arriving, the block can be given
        back and re-allocated -- and a compare-and-swap that names only "whatever bytes are there"
        rewrites the new owner's claim into this session's."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        subnet = str(info.options["subnet"])
        generation = str(info.options["generation"])
        # s1's record still names the block; the block is s2's now.
        for unit_key in list(_flat_claims(etcd)):
            etcd.store[f"network/ipam/allocated/{unit_key}"] = _claim("s2", subnet, "g2")

        assert not await plugin._subnet_allocator.promote(
            subnet, "s1", generation, {_META_KEY: etcd.store[_META_KEY]}
        )

        assert await plugin._subnet_allocator.holder(subnet) == "s2", (
            "it rewrote another session's claim into this one's"
        )

    async def test_a_reuse_that_cannot_take_its_allocation_hands_back_nothing(self) -> None:
        """A promotion that fails must stop the reuse, not merely log.

        Aimed past `_still_ours`, which only asks who owns the units: here s1 still owns them, but
        they record a DIFFERENT block, so the record names an allocation this session does not
        hold in the shape it thinks. Without the check the reuse hands back a NetworkInfo whose
        data plane is built on that record.
        """
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        subnet = str(info.options["subnet"])
        for unit_key in list(_flat_claims(etcd)):
            etcd.store[f"network/ipam/allocated/{unit_key}"] = _claim("s1", "10.99.0.0/24")
        assert await plugin._subnet_allocator.holder(subnet) == "s1", "premise: still s1's units"

        assert await plugin._existing_allocation(cast(AsyncEtcd, etcd), "s1", []) is None

    async def test_an_extra_unstamped_claim_of_a_live_session_is_reclaimed(self) -> None:
        """Compatibility is not use. A session whose record names subnet A can carry a second,
        older claim on B under the same id: unstamped, so compatible with every incarnation, so
        read as live -- while nothing promotes it (promotion follows the record) and nothing
        reclaims it. It stays for the life of the cluster."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        stray = "10.128.99.0/24"
        etcd.store[_allocated_key(stray)] = _claim("s1", stray)
        stray_vni = 9999
        etcd.store[f"network/ipam/vni/{stray_vni}"] = json.dumps({"session_id": "s1"})

        await plugin.reconcile_pool()

        assert _allocated_key(stray) not in etcd.store, "a claim the record never named was kept"
        assert f"network/ipam/vni/{stray_vni}" not in etcd.store

    async def test_it_promotes_a_session_once_however_many_units_it_holds(self) -> None:
        # A wide block is many units; queueing a promotion per unit re-reads the whole pool each
        # time, which is quadratic in the number of legacy sessions.
        class _CountingPoolReads(FakeEtcd):
            def __init__(self) -> None:
                super().__init__()
                self.pool_reads = 0

            @override
            async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
                if prefix == "network/ipam/allocated":
                    self.pool_reads += 1
                return await super().get_prefix(prefix, **kwargs)

        etcd = _CountingPoolReads()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "endpoints": [], "subnet": None}
        )
        subnet = str(info.options["subnet"])
        for unit_key in list(_flat_claims(etcd)):
            etcd.store[f"network/ipam/allocated/{unit_key}"] = _claim("s1", subnet)
        etcd.pool_reads = 0

        await plugin.reconcile_pool()

        assert etcd.pool_reads <= 3, f"it read the whole pool {etcd.pool_reads} times"

    async def test_a_legacy_child_key_of_a_gone_session_is_reclaimed(self) -> None:
        """The mirror of the rule above. An unstamped key is compatible with every incarnation,
        so where a record EXISTS it is live and stays -- but where there is no record at all,
        nothing under the id is live, and skipping it leaves it forever."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        # Written before the field, by a session whose record is long gone.
        etcd.store[member_key("s-old", "a1")] = json.dumps({
            "host_ip": "10.0.0.1",
            "vtep_ip": "10.0.0.1",
            "joined": True,
        })

        await plugin.reconcile_pool()

        assert member_key("s-old", "a1") not in etcd.store

    async def test_a_legacy_child_key_of_a_live_session_is_kept(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        etcd.store[member_key("s1", "a1")] = json.dumps({
            "host_ip": "10.0.0.1",
            "vtep_ip": "10.0.0.1",
            "joined": True,
        })

        await plugin.reconcile_pool()

        assert member_key("s1", "a1") in etcd.store

    async def test_it_reads_each_sessions_record_once(self) -> None:
        # One read per session, not one per claim: a wide block is many units, and a startup
        # sweep on a large pool is a lot of round trips to make twice.
        class _CountingReads(FakeEtcd):
            def __init__(self) -> None:
                super().__init__()
                self.meta_reads = 0

            @override
            async def get(self, key: str, **kwargs: Any) -> str | None:
                if key == _META_KEY:
                    self.meta_reads += 1
                return await super().get(key, **kwargs)

        etcd = _CountingReads()
        plugin = _plugin_with(etcd)
        await plugin.create_network(
            identifier="s1", options={"forced_backend": "vxlan", "endpoints": []}
        )
        etcd.meta_reads = 0

        await plugin.reconcile_pool()

        assert etcd.meta_reads <= 2, f"it read one session's record {etcd.meta_reads} times"

    async def test_what_it_could_not_record_is_reported(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        assert plugin.unrecoverable_leaks() == {}
        plugin._unrecoverable["s1"] = "g1"
        assert plugin.unrecoverable_leaks() == {"s1": "g1"}


class TestWhatSaysAClaimIsInUse:
    """C27. Two ways for a claim to be in use, and every sweep has to know both. The reconciler
    learned them one at a time, and each half on its own is wrong in a different direction: asking
    only about the stamp gave away half of a live session's block, asking only whether the record
    names it gave away the claims of every create still in flight. And the scoped sweep -- the one
    a CREATE runs -- was never taught either."""

    _OPTIONS: dict[str, Any] = {"forced_backend": "vxlan", "endpoints": [], "subnet": None}

    async def test_the_scoped_drain_reclaims_a_stray_unstamped_claim(self) -> None:
        # The same claim `reconcile_pool` reclaims. The two sweeps asked the question separately
        # and so answered it differently, and this is the one a create runs.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        stray = "10.128.99.0/24"
        etcd.store[_allocated_key(stray)] = _claim("s1", stray)
        etcd.store["network/ipam/vni/9999"] = json.dumps({"session_id": "s1"})
        etcd.store["network/cleanup-debt/s1/gone"] = json.dumps({"session_id": "s1"})

        await plugin.drain_cleanup_debt("s1")

        assert _allocated_key(stray) not in etcd.store
        assert "network/ipam/vni/9999" not in etcd.store

    async def test_the_scoped_drain_keeps_the_live_allocation(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        subnet, vni = str(info.options["subnet"]), int(info.options["vni"])
        # Carried over an upgrade: the claims carry no incarnation at all.
        etcd.store[_allocated_key(subnet)] = _claim("s1", subnet)
        etcd.store[f"network/ipam/vni/{vni}"] = json.dumps({"session_id": "s1"})
        etcd.store["network/cleanup-debt/s1/gone"] = json.dumps({"session_id": "s1"})

        await plugin.drain_cleanup_debt("s1")

        assert _allocated_key(subnet) in etcd.store
        assert f"network/ipam/vni/{vni}" in etcd.store

    async def test_a_unit_stamped_with_a_dead_incarnation_of_a_live_block_is_kept(self) -> None:
        """A promotion that could not put back what it had already rewritten leaves a block whose
        units sit on two incarnations -- the code that does it says so. Judged unit by unit, the
        one carrying the superseded incarnation is an orphan; judged by the record, it is half of
        the block a live session is running on. Giving it back puts another tenant there."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(
            identifier="s1",
            options={
                "forced_backend": "vxlan",
                "endpoints": [{"container_id": f"k{i}", "agent_id": "a1"} for i in range(300)],
            },
        )
        subnet = str(info.options["subnet"])
        units = [str(u) for u in ipaddress.ip_network(subnet).subnets(new_prefix=24)]
        assert len(units) > 1, "premise: a block of more than one unit"
        etcd.store[_allocated_key(units[0])] = _claim("s1", subnet)  # unstamped
        etcd.store[_allocated_key(units[1])] = _claim("s1", subnet, "an-older-one")

        await plugin.reconcile_pool()

        assert [u for u in units if _allocated_key(u) in etcd.store] == units

    async def test_an_orphan_sweep_leaves_the_block_the_record_names(self) -> None:
        # The same rule where the release happens rather than where the judgement does: a cleanup
        # for a superseded incarnation must not take a unit the LIVE record names, whatever that
        # unit is stamped with.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        subnet, vni = str(info.options["subnet"]), int(info.options["vni"])
        held = etcd.store[_META_KEY]
        generation = json.loads(held)["generation"]
        # The record moved to a later incarnation, still naming this allocation.
        etcd.store[_META_KEY] = json.dumps({**json.loads(held), "generation": "later"})

        await plugin._sweep_incarnation(cast(AsyncEtcd, etcd), "s1", generation)

        assert _allocated_key(subnet) in etcd.store, "a live session's block was given back"
        assert f"network/ipam/vni/{vni}" in etcd.store, "a live session's vni was given back"


class TestAStrayClaimOfTheLiveIncarnation:
    """C28. The stamp answered for a claim the record does not name. A create that could not take
    the block it already held allocates a second one -- stamped with the live incarnation, named
    by nothing, and so read as live for as long as the session ran. Identity is what the record
    can answer with; the stamp is only for the window before it names anything."""

    _OPTIONS: dict[str, Any] = {"forced_backend": "vxlan", "endpoints": [], "subnet": None}

    async def test_a_stray_claim_carrying_the_live_incarnation_is_reclaimed(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        generation = str(info.options["generation"])
        stray = "10.128.77.0/24"
        etcd.store[_allocated_key(stray)] = _claim("s1", stray, generation)
        etcd.store["network/ipam/vni/8888"] = json.dumps({
            "session_id": "s1",
            "generation": generation,
        })

        await plugin.reconcile_pool()

        assert _allocated_key(stray) not in etcd.store
        assert "network/ipam/vni/8888" not in etcd.store
        assert _allocated_key(str(info.options["subnet"])) in etcd.store, "it took the live one"

    async def test_a_create_that_has_not_published_still_keeps_its_claims(self) -> None:
        # The window the stamp is for: the record names nothing until publish, so identity cannot
        # answer, and a sweep that asked it anyway reclaimed the claims of every create in flight.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        held, _ = await plugin._claim_session(cast(AsyncEtcd, etcd), "s1", "tok", [])
        generation = json.loads(held)["generation"]
        await plugin._subnet_allocator.acquire("s1", generation=generation)
        await plugin._vni_allocator.acquire("s1", generation)

        assert await plugin.reconcile_pool() == 0

    async def test_a_stale_stamped_unit_of_a_named_block_is_taken_not_just_kept(self) -> None:
        """Keeping it stops the block being handed to another tenant, and leaves it answering to
        two cleanups for as long as the session lives. The record names the block and the guard
        pins the record, so the promotion has something better than a stamp to go on."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        generation = str(info.options["generation"])
        subnet = str(info.options["subnet"])
        vni = int(cast(int, info.options["vni"]))
        etcd.store[_allocated_key(subnet)] = _claim("s1", subnet, "an-older-one")
        etcd.store[f"network/ipam/vni/{vni}"] = json.dumps({
            "session_id": "s1",
            "generation": "an-older-one",
        })

        await plugin.reconcile_pool()

        assert json.loads(etcd.store[_allocated_key(subnet)])["generation"] == generation
        assert json.loads(etcd.store[f"network/ipam/vni/{vni}"])["generation"] == generation

    async def test_it_reads_the_pool_once_however_many_sessions_need_taking(self) -> None:
        # Each promotion used to read the whole pool, so the first start after the incarnation
        # field -- where every session needs one -- cost a full scan per session.
        class _CountingPoolReads(FakeEtcd):
            def __init__(self) -> None:
                super().__init__()
                self.pool_reads = 0

            @override
            async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
                if prefix == "network/ipam/allocated":
                    self.pool_reads += 1
                return await super().get_prefix(prefix, **kwargs)

        etcd = _CountingPoolReads()
        plugin = _plugin_with(etcd)
        sessions = [f"s{i}" for i in range(6)]
        for session_id in sessions:
            info = await plugin.create_network(identifier=session_id, options=dict(self._OPTIONS))
            subnet = str(info.options["subnet"])
            # Carried over an upgrade: every one of them needs promoting.
            etcd.store[_allocated_key(subnet)] = _claim(session_id, subnet)
        etcd.pool_reads = 0

        await plugin.reconcile_pool()

        assert etcd.pool_reads <= 3, (
            f"it read the whole pool {etcd.pool_reads} times for {len(sessions)} sessions"
        )
        for session_id in sessions:
            meta = json.loads(etcd.store[session_meta_key(session_id)])
            claim = json.loads(etcd.store[_allocated_key(str(meta["subnet"]))])
            assert claim.get("generation") == meta["generation"]


class TestAReconciliationPassThatCouldNotRun:
    """C29. The startup sweep was fail-open: a pass that raised was a log line, so one etcd blip
    left orphan claims until the next restart while every health surface read clean."""

    _OPTIONS: dict[str, Any] = {"forced_backend": "vxlan", "endpoints": [], "subnet": None}

    class _PoolUnreadable(FakeEtcd):
        def __init__(self) -> None:
            super().__init__()
            self.refusing = True

        @override
        async def get_prefix(self, prefix: str, **kwargs: Any) -> dict[str, str]:
            if self.refusing and prefix == "network/ipam/allocated":
                raise RuntimeError("etcd is unreachable")
            return await super().get_prefix(prefix, **kwargs)

    async def test_a_failed_pass_stays_owed(self) -> None:
        etcd = self._PoolUnreadable()
        plugin = _plugin_with(etcd)
        assert _owed(plugin) is False

        await plugin._reconcile_pool_reporting()

        assert _owed(plugin) is True

    async def test_the_next_use_of_a_session_id_pays_it(self) -> None:
        etcd = self._PoolUnreadable()
        plugin = _plugin_with(etcd)
        await plugin._reconcile_pool_reporting()
        assert _owed(plugin) is True
        # An orphan claim from a manager life nothing wrote down.
        etcd.refusing = False
        stray = "10.128.55.0/24"
        etcd.store[_allocated_key(stray)] = _claim("s-gone", stray, "g-gone")

        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        assert _owed(plugin) is False
        assert _allocated_key(stray) not in etcd.store, "the orphan waited for a restart"

    async def test_a_pass_that_went_through_is_not_owed(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin._reconcile_pool_reporting()
        assert _owed(plugin) is False


class TestWhoSweepsAndWhen:
    """C30. The sweep was conditional on traffic: it ran at startup and was retried only when a
    session id came round. On a cluster where nobody is starting sessions, that retry never
    arrives. And on a rolling restart every manager swept at once."""

    _OPTIONS: dict[str, Any] = {"forced_backend": "vxlan", "endpoints": [], "subnet": None}

    async def test_the_first_manager_takes_the_turn_and_the_rest_skip(self) -> None:
        etcd = FakeEtcd()
        first = _plugin_with(etcd)
        second = _plugin_with(etcd)

        assert await first._claim_reconcile_turn() is True
        assert await second._claim_reconcile_turn() is False, (
            "every manager in an HA set swept the whole pool at the same moment"
        )

    async def test_the_turn_comes_round_again_once_the_interval_has_passed(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        assert await plugin._claim_reconcile_turn() is True
        etcd.store[cni._RECONCILE_TICKET] = json.dumps({
            "at": time.time() - cni._RECONCILE_INTERVAL_SEC - 1,
            "by": "someone",
        })

        assert await plugin._claim_reconcile_turn() is True

    async def test_an_unreadable_ticket_does_not_stop_the_sweep(self) -> None:
        # Fails open: a pass too many costs a pool read, a pass too few is a claim nobody
        # reclaims.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        etcd.store[cni._RECONCILE_TICKET] = "null"

        assert await plugin._claim_reconcile_turn() is True


class TestOneUnreadableKeyDoesNotStopTheSweep:
    """C31. Every value under these prefixes is written here as a JSON object, and the code read
    them back as one without checking. Syntactically valid JSON that is not an object raises
    AttributeError, not ValueError -- so one hand-edited or half-written key aborted the whole
    reconciliation pass, for good."""

    _OPTIONS: dict[str, Any] = {"forced_backend": "vxlan", "endpoints": [], "subnet": None}

    async def test_a_pool_claim_that_is_not_an_object_is_stepped_over(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        etcd.store[_allocated_key("10.128.90.0/24")] = "null"
        etcd.store[_allocated_key("10.128.91.0/24")] = "[]"
        etcd.store["network/ipam/vni/7777"] = "12345"
        # And a real orphan behind them, which the sweep must still reach.
        stray = "10.128.92.0/24"
        etcd.store[_allocated_key(stray)] = _claim("s-gone", stray, "g-gone")

        await plugin.reconcile_pool()

        assert _allocated_key(stray) not in etcd.store, "one bad key stopped the whole sweep"

    async def test_a_session_record_that_is_not_an_object_does_not_wedge_the_id(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        etcd.store[session_meta_key("s1")] = "[]"

        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))

        assert info.options["subnet"]

    async def test_a_destroy_removes_a_record_it_cannot_read(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        etcd.store[session_meta_key("s1")] = "null"

        await plugin.destroy_network("s1")

        assert session_meta_key("s1") not in etcd.store


class TestARecordThatIsAnObjectButNotAnAllocation:
    """C32. Being a JSON object is not being a usable record. ``{"vni": []}`` is an object, and
    ``int([])`` raises TypeError -- which no parse site was catching, so such a key stopped
    whatever pass reached it just as surely as a non-object did."""

    _OPTIONS: dict[str, Any] = {"forced_backend": "vxlan", "endpoints": [], "subnet": None}

    async def test_a_corrupted_record_does_not_cost_the_session_its_allocation(self) -> None:
        """The one that matters. `{"vni": []}` has the key, so the sweep judged by identity;
        identity read no VNI out of it, decided the session's real claim was not the one its
        record named, and gave a LIVE VXLAN's VNI back to the pool under an exact-record guard --
        for the next session to be handed. Preserving is the only safe answer to a record nobody
        can read."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        subnet, vni = str(info.options["subnet"]), int(cast(int, info.options["vni"]))
        record = json.loads(etcd.store[session_meta_key("s1")])
        etcd.store[session_meta_key("s1")] = json.dumps({**record, "vni": []})

        await plugin.reconcile_pool()

        assert f"network/ipam/vni/{vni}" in etcd.store, "a live session's vni went back to the pool"
        assert _allocated_key(subnet) in etcd.store, "a live session's subnet went back to the pool"

    async def test_a_corrupted_record_stops_an_orphan_sweep_of_that_session(self) -> None:
        # The same rule where the release happens rather than where the judgement does: what a
        # cleanup must keep its hands off is what the LIVE record names, and that cannot be read.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        subnet, vni = str(info.options["subnet"]), int(cast(int, info.options["vni"]))
        record = json.loads(etcd.store[session_meta_key("s1")])
        generation = str(record["generation"])
        etcd.store[session_meta_key("s1")] = json.dumps({
            **record,
            "subnet": ["not", "a", "subnet"],
            "generation": "later",
        })

        assert await plugin._sweep_incarnation(cast(AsyncEtcd, etcd), "s1", generation) is False

        assert f"network/ipam/vni/{vni}" in etcd.store
        assert _allocated_key(subnet) in etcd.store

    async def test_a_vni_that_is_not_a_number_does_not_stop_the_sweep(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        record = json.loads(etcd.store[session_meta_key("s1")])
        etcd.store[session_meta_key("s1")] = json.dumps({**record, "vni": []})
        stray = "10.128.93.0/24"
        etcd.store[_allocated_key(stray)] = _claim("s-gone", stray, "g-gone")

        await plugin.reconcile_pool()

        assert _allocated_key(stray) not in etcd.store

    async def test_a_subnet_that_is_not_a_network_is_not_reused(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        record = json.loads(etcd.store[session_meta_key("s1")])
        etcd.store[session_meta_key("s1")] = json.dumps({
            **record,
            "subnet": "not-a-network",
            "_state": "ready",
        })

        assert await plugin._existing_allocation(cast(AsyncEtcd, etcd), "s1", []) is None

    async def test_a_record_with_no_subnet_at_all_is_not_reused(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        etcd.store[session_meta_key("s1")] = json.dumps({"_state": "ready", "generation": "g1"})

        assert await plugin._existing_allocation(cast(AsyncEtcd, etcd), "s1", []) is None


class TestTheRecordContractNotJustTheParse:
    """C35. The first cut asked only whether a value PARSED. `vni: null` parses, `vni: true`
    parses to 1, `vni: 0` and `vni: 16777216` are integers, and a public or IPv6 subnet is a
    network. Each of them makes a live session's real claim look like one its record does not
    name -- which is the sweep's cue to give it back to the pool. The bar is the contract the
    agent's privnet policy already holds the manager to."""

    _OPTIONS: dict[str, Any] = {"forced_backend": "vxlan", "endpoints": [], "subnet": None}

    async def _live(self, etcd: FakeEtcd, plugin: CNINetworkPlugin) -> tuple[str, int]:
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        return str(info.options["subnet"]), int(cast(int, info.options["vni"]))

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("vni", None),  # a vxlan session that names no vni
            ("vni", True),  # bool is an int subclass; int(True) is 1
            ("vni", 1.5),  # int() truncates
            ("vni", 0),  # below the 24-bit range
            ("vni", 1 << 24),  # above it
            ("vni", "not-a-vni"),
            ("subnet", None),
            ("subnet", "8.8.8.0/24"),  # public
            ("subnet", "fd00::/64"),  # not IPv4
            ("subnet", "10.128.0.1/24"),  # not aligned to its own prefix
            ("backend", "something-else"),
        ],
    )
    async def test_a_live_session_keeps_its_allocation(self, field: str, value: Any) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        subnet, vni = await self._live(etcd, plugin)
        record = json.loads(etcd.store[session_meta_key("s1")])
        etcd.store[session_meta_key("s1")] = json.dumps({**record, field: value})

        await plugin.reconcile_pool()

        assert f"network/ipam/vni/{vni}" in etcd.store, f"{field}={value!r} cost a live vni"
        assert _allocated_key(subnet) in etcd.store, f"{field}={value!r} cost a live subnet"

    async def test_a_non_vxlan_record_that_names_a_vni_is_not_acted_on(self) -> None:
        # The coupling the other way round: only a vxlan session has a VNI, so one on any other
        # backend is a record nobody should judge from.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        subnet, vni = await self._live(etcd, plugin)
        record = json.loads(etcd.store[session_meta_key("s1")])
        etcd.store[session_meta_key("s1")] = json.dumps({**record, "backend": "bridge"})

        await plugin.reconcile_pool()

        assert f"network/ipam/vni/{vni}" in etcd.store

    async def test_a_record_that_does_not_name_a_valid_allocation_is_not_reused(self) -> None:
        """The reuse path has to use the SAME parser. It did not, so a record the sweep called
        corrupt was still handed to the agents -- which refuse it, and every retry refused it
        again."""
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await self._live(etcd, plugin)
        record = json.loads(etcd.store[session_meta_key("s1")])
        etcd.store[session_meta_key("s1")] = json.dumps({**record, "vni": None})

        assert await plugin._existing_allocation(cast(AsyncEtcd, etcd), "s1", []) is None

    async def test_a_valid_allocation_is_still_reused(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        subnet, vni = await self._live(etcd, plugin)

        reused = await plugin._existing_allocation(cast(AsyncEtcd, etcd), "s1", [])

        assert reused is not None
        assert reused.options["subnet"] == subnet
        assert reused.options["vni"] == vni

    async def test_a_creating_record_that_has_allocated_nothing_is_not_corrupt(self) -> None:
        # PENDING is not CORRUPT: a record that has claimed the id and named nothing yet is what
        # every create holds before it publishes.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        held, _ = await plugin._claim_session(cast(AsyncEtcd, etcd), "s1", "tok", [])
        generation = json.loads(held)["generation"]
        await plugin._subnet_allocator.acquire("s1", generation=generation)
        await plugin._vni_allocator.acquire("s1", generation)

        assert await plugin.reconcile_pool() == 0


class _SlowSweep(CNINetworkPlugin):
    """A plugin whose reconciliation pass takes as long as the test wants it to."""

    sweeping: asyncio.Event
    finish: asyncio.Event

    def __init__(self, plugin_config: dict[str, Any], local_config: dict[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self.sweeping = asyncio.Event()
        self.finish = asyncio.Event()

    @override
    async def _reconcile_pool_reporting(self) -> None:
        self.sweeping.set()
        await self.finish.wait()


class TestTheReconcileTicketAndTheClock:
    """C33. Managers compare wall clocks on the ticket, so one running ahead could park the whole
    cluster's reconciliation for as long as its clock is ahead."""

    async def test_a_ticket_dated_in_the_future_is_not_trusted(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        etcd.store[cni._RECONCILE_TICKET] = json.dumps({
            "at": time.time() + cni._RECONCILE_INTERVAL_SEC * 10,
            "by": "a-fast-clock",
        })

        assert await plugin._claim_reconcile_turn() is True

    async def test_the_interval_runs_from_when_the_sweep_finished(self) -> None:
        # Dated from the start, a sweep that outlasts the interval lets the next manager take a
        # turn while this one is still walking the pool.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        assert await plugin._claim_reconcile_turn() is True
        aged = json.dumps({
            "at": time.time() - cni._RECONCILE_INTERVAL_SEC - 1,
            "by": plugin._reconcile_token,
        })
        etcd.store[cni._RECONCILE_TICKET] = aged
        plugin._reconcile_ticket = aged

        assert await plugin._hold_reconcile_turn() is True

        assert await _plugin_with(etcd)._claim_reconcile_turn() is False

    async def test_a_long_sweep_keeps_the_turn_while_it_runs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The ticket is a timestamp, so a pass that outlasts the interval leaves an expired one
        behind it and the next manager starts a second full scan over the top. Re-dating only at
        the END could not prevent that -- which is what the comment claimed and the code did
        not."""
        etcd = FakeEtcd()
        plugin = _SlowSweep({}, {})
        _wire(plugin, etcd)
        monkeypatch.setattr("ai.backend.manager.network.cni._RECONCILE_HEARTBEAT_SEC", 0.01)

        assert await plugin._claim_reconcile_turn() is True
        first = etcd.store[cni._RECONCILE_TICKET]
        sweep = asyncio.create_task(plugin._sweep_holding_the_turn())
        await plugin.sweeping.wait()
        await asyncio.sleep(0.05)
        beaten = etcd.store[cni._RECONCILE_TICKET]
        plugin.finish.set()
        await sweep

        assert beaten != first, "the turn was not re-dated while the sweep ran"

    async def test_a_long_sweep_does_not_stamp_over_the_turn_it_lost(self) -> None:
        """A sweep that outlasts the interval loses the turn to the next manager. Re-dating
        unconditionally then put the first manager's ticket back over the second's, and the two
        traded the turn back and forth while both scanned the pool."""
        etcd = FakeEtcd()
        slow = _plugin_with(etcd)
        assert await slow._claim_reconcile_turn() is True
        # The interval passes while `slow` is still walking, and another manager takes the turn.
        etcd.store[cni._RECONCILE_TICKET] = json.dumps({
            "at": time.time() - cni._RECONCILE_INTERVAL_SEC - 1,
            "by": slow._reconcile_token,
        })
        other = _plugin_with(etcd)
        assert await other._claim_reconcile_turn() is True
        taken = etcd.store[cni._RECONCILE_TICKET]

        assert await slow._hold_reconcile_turn() is False, "it stamped over the new turn"
        assert etcd.store[cni._RECONCILE_TICKET] == taken


class TestADestroyThatFindsNoRecordAtAll:
    """C7b. "No record" is what the destroy READ, not something it holds. A create claims the id
    with a compare-and-swap on that same key, so between the read and any delete it can publish a
    whole session -- whose keys the sweep then takes and whose subnet and VNI it gives back while
    the create is still handing them to its agents."""

    class _CreateLandsOnTheRead(FakeEtcd):
        """A store that lets a create claim the id while the destroy is reading it."""

        def __init__(self) -> None:
            super().__init__()
            self.claim: str | None = None

        @override
        async def get(self, key: str, **kwargs: Any) -> str | None:
            found = await super().get(key, **kwargs)
            if key == _META_KEY and self.claim is not None:
                # The create wins the moment the destroy has read "absent" and not before.
                self.store[key] = self.claim
                self.claim = None
            return found

    async def test_it_does_not_sweep_a_create_that_landed_first(self) -> None:
        etcd = self._CreateLandsOnTheRead()
        plugin = _plugin_with(etcd)
        etcd.claim = json.dumps({
            "_owner": "tok1",
            "_state": "creating",
            "_claimed_at": time.time(),
        })
        # What that create has already claimed but not yet published.
        await plugin._subnet_allocator.acquire("s1")
        await plugin._vni_allocator.acquire("s1")

        with pytest.raises(OverlayTeardownPending):
            await plugin.destroy_network("s1")

        assert await plugin._subnet_allocator.holder("10.128.0.0/24") == "s1"
        assert json.loads(etcd.store[_META_KEY])["_state"] == "creating", (
            "it wrote over the record the create rolls back from"
        )

    async def test_it_still_sweeps_what_nothing_is_building_on(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin._subnet_allocator.acquire("s1")
        await plugin._vni_allocator.acquire("s1")

        await plugin.destroy_network("s1")

        assert _pool_claims(etcd) == []
        assert _META_KEY not in etcd.store


class TestAClaimNoRecordEverNamed:
    """C8. A create cancelled between claiming a block and publishing the record that would have
    named it leaves the pool holding something no meta mentions. Releasing what the record names
    cannot reach it; releasing what the POOL says is this session's can."""

    async def test_the_rollback_gives_it_back(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        await plugin._subnet_allocator.acquire("s1")
        await plugin._vni_allocator.acquire("s1")
        held = json.dumps({"_owner": "tok1", "_state": "creating", "_claimed_at": time.time()})
        etcd.store[_META_KEY] = held

        # The create knows of neither: it was cancelled before either reached its local variables.
        await plugin._rollback_create("s1", None, None, held)

        assert _pool_claims(etcd) == []
        assert _META_KEY not in etcd.store


class TestAnAddressWithNoEndpointRecord:
    """C3. The address claim and the endpoint record are two writes. Everything downstream reads
    the record -- peers program FDB and ARP from it, the resolver answers from it -- so a
    container holding an address no record mentions is one its own session cannot reach, on a
    session that reports itself healthy."""

    async def test_a_retry_writes_the_record_the_first_attempt_owed(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        # Exactly what a manager killed between the two writes leaves behind.
        etcd.store["network/session/s1/ipam/10.128.0.1"] = json.dumps({"container_id": "k1"})

        ip, _mac = await plugin._endpoint_allocator.assign(
            "s1", "k1", "10.128.0.0/24", agent_id="a1", cluster_hostname="main1"
        )

        assert ip == "10.128.0.1"
        record = json.loads(etcd.store["network/session/s1/endpoints/k1"])
        assert record["ip"] == "10.128.0.1"
        assert record["agent_id"] == "a1"

    async def test_it_does_not_take_a_second_address(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        etcd.store["network/session/s1/ipam/10.128.0.1"] = json.dumps({"container_id": "k1"})

        await plugin._endpoint_allocator.assign(
            "s1", "k1", "10.128.0.0/24", agent_id="a1", cluster_hostname=None
        )

        addresses = [k for k in etcd.store if k.startswith("network/session/s1/ipam/")]
        assert addresses == ["network/session/s1/ipam/10.128.0.1"]


class TestAMetaThatOutlivedItsAllocation:
    """C4. A rollback that frees the subnet and VNI but cannot delete the session's keys leaves a
    record naming resources the pool is free to hand to the next session."""

    async def test_a_record_whose_allocation_is_gone_is_not_reused(self) -> None:
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        first = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})
        # Free the allocation behind the record's back, as a half-failed rollback does, and let
        # another session take it. Released under the incarnation that claimed it -- ownership is
        # (session, incarnation), so naming the session alone releases nothing.
        generation = str(first.options["generation"])
        await plugin._subnet_allocator.release(first.options["subnet"], "s1", generation)
        await plugin._vni_allocator.release(int(first.options["vni"]), "s1", generation)
        stolen = await plugin._subnet_allocator.acquire("s2")
        assert stolen == first.options["subnet"]

        again = await plugin.create_network(identifier="s1", options={"forced_backend": "vxlan"})

        assert again.options["subnet"] != stolen, (
            "s1 was handed the subnet s2 now holds, from a record that outlived its allocation"
        )

    async def test_a_rollback_that_cannot_clear_the_record_keeps_the_allocation(self) -> None:
        class NoDeletes(FakeEtcd):
            @override
            async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
                raise RuntimeError("etcd is unreachable")

        etcd = NoDeletes()
        plugin = _plugin_with(etcd)
        subnet = await plugin._subnet_allocator.acquire("s1")
        vni = await plugin._vni_allocator.acquire("s1")
        # The exact bytes the create holds: everything it does afterwards is conditional on them.
        record = json.dumps({"subnet": subnet, "vni": vni, "_owner": "mine", "_state": "creating"})
        etcd.store["network/session/s1/meta"] = record

        await plugin._rollback_create("s1", subnet, vni, record)

        # Nothing was released, so nothing else can be given what the surviving record names.
        assert await plugin._subnet_allocator.holder(subnet) == "s1"
        assert await plugin._vni_allocator.holder(vni) == "s1"
        assert await plugin._subnet_allocator.acquire("s2") != subnet


class TestAllocationRoundTrips:
    """C6. Claiming the Nth session must not cost N round trips.

    The plain low-to-high scan issued one compare-and-swap per block already taken, so a cluster
    with a few hundred live sessions spent that many etcd calls on every launch -- quadratic over
    the pool's lifetime. Reading the pool once rules candidates out; the CAS still decides.
    """

    class _Counting(FakeEtcd):
        """Counts every compare-and-swap the pool costs, whichever primitive makes it: a claim is
        a guarded `compare_and_put` now, and counting only `put_if_absent` would report a scan
        over the taken blocks as free."""

        def __init__(self) -> None:
            super().__init__()
            self.cas = 0

        @override
        async def put_if_absent(self, key: str, val: str, **kwargs: Any) -> bool:
            self.cas += 1
            return await super().put_if_absent(key, val, **kwargs)

        @override
        async def compare_and_put(self, key: str, val: str, **kwargs: Any) -> bool:
            self.cas += 1
            return await super().compare_and_put(key, val, **kwargs)

    async def test_the_hundredth_session_costs_what_the_first_did(self) -> None:
        etcd = self._Counting()
        subnets = SubnetAllocator(cast(AsyncEtcd, etcd))
        vnis = VNIAllocator(cast(AsyncEtcd, etcd))
        for i in range(100):
            await subnets.acquire(f"s{i}")
            await vnis.acquire(f"s{i}")
        before = etcd.cas
        await subnets.acquire("s100")
        await vnis.acquire("s100")
        assert etcd.cas - before == 2, (
            "one compare-and-swap each; anything more is a scan over the taken blocks"
        )


class _MetaBlindEtcd(FakeEtcd):
    """A store whose session meta reads come back empty until released.

    That is the window the race lives in: both managers look for an existing session, both are
    told there is none, and both go on to build one.
    """

    def __init__(self, gate: asyncio.Event) -> None:
        super().__init__()
        self._gate = gate

    @override
    async def get(self, key: str, **kwargs: Any) -> str | None:
        if key.endswith("/meta") and not self._gate.is_set():
            return None
        return await super().get(key, **kwargs)


class TestACreateThatFailedBesideOneThatDidNot:
    """C1, the other half. Two managers building one session share the subnet and the VNI they
    converge on, so "undo what I did" is only meaningful against a record saying whose it is.
    Without that, the one that failed released the allocation the one that succeeded had already
    handed to its agents -- and the pool was free to give that VNI to the next session, while the
    caller of the successful create went on believing it had a network."""

    _OPTIONS = {
        "forced_backend": "vxlan",
        "endpoints": [{"container_id": "k1", "agent_id": "a1"}],
    }

    async def _one_fails_beside_one_that_works(self) -> tuple[FakeEtcd, Any]:
        gate = asyncio.Event()
        etcd = _MetaBlindEtcd(gate)
        reached = asyncio.Event()

        class FailsAtTheLastStep(CNINetworkPlugin):
            @override
            async def _preseed_members(
                self,
                session_id: str,
                member_agents: list[str],
                generation: str | None = None,
                held: str | None = None,
            ) -> None:
                reached.set()
                await asyncio.sleep(0.05)
                raise RuntimeError("this create was cancelled")

        loser = _wire(FailsAtTheLastStep({}, {}), etcd)
        winner = _plugin_with(etcd)
        failing = asyncio.create_task(
            loser.create_network(identifier="s1", options=dict(self._OPTIONS))
        )
        await reached.wait()
        gate.set()
        good = await winner.create_network(identifier="s1", options=dict(self._OPTIONS))
        with pytest.raises(RuntimeError):
            await failing
        return etcd, good

    async def test_the_successful_session_keeps_its_record(self) -> None:
        etcd, _good = await self._one_fails_beside_one_that_works()
        assert "network/session/s1/meta" in etcd.store
        assert "network/session/s1/endpoints/k1" in etcd.store

    async def test_the_successful_session_keeps_its_allocation(self) -> None:
        etcd, good = await self._one_fails_beside_one_that_works()
        plugin = _plugin_with(etcd)
        assert await plugin._subnet_allocator.holder(good.options["subnet"]) == "s1"
        assert await plugin._vni_allocator.holder(int(good.options["vni"])) == "s1"

    async def test_what_it_hands_back_carries_no_bookkeeping(self) -> None:
        # `_owner` and `_state` are the create's own; a caller threading them into a kernel's
        # network config would be passing our internals to the agents.
        etcd = FakeEtcd()
        plugin = _plugin_with(etcd)
        info = await plugin.create_network(identifier="s1", options=dict(self._OPTIONS))
        assert not [key for key in info.options if key.startswith("_")]


class TestABlockClaimedOnlyInPart:
    """C1, wide blocks. A subnet wider than one unit is claimed a unit at a time, so an acquire
    that died between them leaves a block that is half this session's and half free. Answering
    "this session already holds it" on the strength of one unit hands back a /23 whose second
    half nothing holds -- and the pool gives that half to the next session, overlapping the
    address space of one that believes it has the lot."""

    @staticmethod
    def _half_claimed(etcd: FakeEtcd, session_id: str, block: str, unit: str) -> None:
        etcd.store[_allocated_key(unit)] = _claim(session_id, block)

    async def test_a_partial_claim_is_finished_not_adopted(self) -> None:
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        self._half_claimed(etcd, "s1", "10.128.0.0/23", "10.128.0.0/24")

        got = await allocator.acquire("s1", host_count=400)

        assert got == "10.128.0.0/23"
        assert _allocated_key("10.128.1.0/24") in etcd.store, "the second half was never claimed"

    async def test_the_finished_block_is_not_offered_to_anyone_else(self) -> None:
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        self._half_claimed(etcd, "s1", "10.128.0.0/23", "10.128.0.0/24")
        await allocator.acquire("s1", host_count=400)

        assert await allocator.acquire("s2") not in ("10.128.0.0/24", "10.128.1.0/24")

    async def test_a_partial_claim_another_session_broke_into_is_given_back(self) -> None:
        # It can never be this session's now, and holding the rest of it helps nobody.
        etcd = FakeEtcd()
        allocator = _subnet_allocator(etcd)
        self._half_claimed(etcd, "s1", "10.128.0.0/23", "10.128.0.0/24")
        etcd.store[_allocated_key("10.128.1.0/24")] = _claim("s2", "10.128.1.0/24")

        got = await allocator.acquire("s1", host_count=400)

        assert got != "10.128.0.0/23"
        assert _allocated_key("10.128.0.0/24") not in etcd.store, "the dead half was kept"
        assert await allocator.holder("10.128.1.0/24") == "s2"

    async def test_an_acquire_that_is_cancelled_keeps_no_units(self) -> None:
        # Without this the units it had already won stay claimed with nobody behind them.
        started = asyncio.Event()

        class StallsBetweenUnits(FakeEtcd):
            @override
            async def compare_and_put(self, key: str, val: str, **kwargs: Any) -> bool:
                claimed = await super().compare_and_put(key, val, **kwargs)
                if claimed and not started.is_set():
                    started.set()
                    await asyncio.sleep(60)
                return claimed

        etcd = StallsBetweenUnits()
        allocator = _subnet_allocator(etcd)
        task = asyncio.create_task(allocator.acquire("s1", host_count=400))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert not [k for k in etcd.store if k.startswith("network/ipam/allocated/")]

    async def test_a_unit_that_would_not_go_back_does_not_hold_up_the_rest(self) -> None:
        # Giving a partial claim back is best-effort per unit -- the caller is on its way to the
        # next candidate block -- but stopping at the first etcd hiccup would leave the units
        # after it claimed by a session whose meta names a different subnet, and no later release
        # names them. The failure is logged; the rest still go back.
        class _RefusesTheFirstDelete(FakeEtcd):
            def __init__(self) -> None:
                super().__init__()
                self.attempted: list[str] = []

            @override
            async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
                self.attempted.append(key)
                if len(self.attempted) == 1:
                    raise RuntimeError("etcd is unreachable")
                return await super().delete_if_value(key, expected, **kwargs)

        etcd = _RefusesTheFirstDelete()
        allocator = _subnet_allocator(etcd)
        units = ["10.128.0.0/24", "10.128.1.0/24"]
        payload = _claim("s1", "10.128.0.0/23")
        for unit in units:
            etcd.store[_allocated_key(unit)] = payload

        await allocator._give_back(units, payload)

        assert etcd.attempted == [_allocated_key(unit) for unit in units], "it stopped at the first"
        assert _allocated_key("10.128.1.0/24") not in etcd.store

    async def test_a_claim_that_cannot_be_given_back_fails_the_acquire(self) -> None:
        # The units it could not release are named by no meta and released by nothing later, so
        # moving on to the next block would report a healthy session over a pool that has shrunk.
        class _RefusesDeletes(FakeEtcd):
            @override
            async def delete_if_value(self, key: str, expected: str, **kwargs: Any) -> bool:
                raise RuntimeError("etcd is unreachable")

        etcd = _RefusesDeletes()
        allocator = _subnet_allocator(etcd)
        # The second unit of the block went to somebody else between the pool read and the CAS.
        etcd.store[_allocated_key("10.128.1.0/24")] = _claim("s2", "10.128.1.0/24")

        with pytest.raises(SubnetClaimStranded):
            await allocator._try_claim_units(
                ipaddress.ip_network("10.128.0.0/23"), _claim("s1", "10.128.0.0/23")
            )
