"""Unit tests for the native veth/bridge attach runner (BEP-1062)."""

import asyncio
from pathlib import Path
from typing import Any

import pytest

import ai.backend.agent.network.native_attacher as na
from ai.backend.agent.errors.network import (
    NetworkStateStoreConflict,
    StaticAddressUnavailable,
    SubnetAddressPoolExhausted,
)
from ai.backend.agent.network.native_attacher import (
    HostLocalIpam,
    NativeBridgeAttachRunner,
    _veth_name,
    get_host_local_ipam,
)

_NETNS = "/proc/4242/ns/net"
_STATIC_CFG = {
    "type": "bridge",
    "bridge": "baimulti4097",
    "mtu": 1450,
    "isGateway": False,
    "ipMasq": False,
    "ipam": {"type": "static", "addresses": [{"address": "10.128.5.7/24"}]},
}
_LOCAL_CFG = {
    "type": "bridge",
    "bridge": "bailo4097",
    "isGateway": True,
    "isDefaultGateway": True,
    "ipMasq": True,
    "ipam": {"type": "host-local", "subnet": "172.30.1.0/24"},
}


class TestHostLocalIpam:
    async def test_allocates_skipping_reserved(self, tmp_path: Path) -> None:
        ipam = HostLocalIpam(tmp_path)
        # .1 is reserved (gateway); first free host is .2
        ip = await ipam.allocate("172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"])
        assert ip == "172.30.1.2"

    async def test_allocation_is_idempotent_per_owner(self, tmp_path: Path) -> None:
        ipam = HostLocalIpam(tmp_path)
        first = await ipam.allocate("172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"])
        again = await ipam.allocate("172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"])
        assert first == again

    async def test_distinct_owners_get_distinct_ips(self, tmp_path: Path) -> None:
        ipam = HostLocalIpam(tmp_path)
        a = await ipam.allocate("172.30.1.0/24", "cidA", "eth0", reserve=["172.30.1.1"])
        b = await ipam.allocate("172.30.1.0/24", "cidB", "eth0", reserve=["172.30.1.1"])
        assert a != b

    async def test_release_frees_the_address(self, tmp_path: Path) -> None:
        ipam = HostLocalIpam(tmp_path)
        await ipam.allocate("172.30.1.0/24", "cidA", "eth0", reserve=["172.30.1.1"])
        remaining = await ipam.release("172.30.1.0/24", "cidA", "eth0")
        assert remaining == 0
        # freed address is reusable
        reused = await ipam.allocate("172.30.1.0/24", "cidB", "eth0", reserve=["172.30.1.1"])
        assert reused == "172.30.1.2"

    async def test_pool_exhaustion_raises(self, tmp_path: Path) -> None:
        ipam = HostLocalIpam(tmp_path)
        # /30 has exactly two hosts; the gateway takes one
        await ipam.allocate("10.0.0.0/30", "cidA", "eth0", reserve=["10.0.0.1"])
        with pytest.raises(SubnetAddressPoolExhausted):
            await ipam.allocate("10.0.0.0/30", "cidB", "eth0", reserve=["10.0.0.1"])

    async def test_a_requested_address_is_pinned(self, tmp_path: Path) -> None:
        # Single-node cluster peers land on the deterministic address /etc/hosts advertises.
        ipam = HostLocalIpam(tmp_path)
        ip = await ipam.allocate(
            "172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"], requested="172.30.1.9"
        )
        assert ip == "172.30.1.9"

    async def test_a_requested_address_is_idempotent(self, tmp_path: Path) -> None:
        ipam = HostLocalIpam(tmp_path)
        a = await ipam.allocate(
            "172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"], requested="172.30.1.9"
        )
        b = await ipam.allocate(
            "172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"], requested="172.30.1.9"
        )
        assert a == b == "172.30.1.9"

    async def test_a_requested_address_already_taken_is_refused(self, tmp_path: Path) -> None:
        # Two kernels never request the same IP by design, but if they did it must fail loudly
        # rather than silently double-assign.
        ipam = HostLocalIpam(tmp_path)
        await ipam.allocate(
            "172.30.1.0/24", "cidA", "eth0", reserve=["172.30.1.1"], requested="172.30.1.9"
        )
        with pytest.raises(StaticAddressUnavailable):
            await ipam.allocate(
                "172.30.1.0/24", "cidB", "eth0", reserve=["172.30.1.1"], requested="172.30.1.9"
            )

    async def test_an_owner_holding_another_address_is_refused_not_silently_kept(
        self, tmp_path: Path
    ) -> None:
        # A re-attach whose DEL never landed (container_id is the kernel id, stable across a
        # restart) must not quietly keep the old, dynamic address: its peers' /etc/hosts already
        # names the pinned one, so the kernel would be unreachable under the name they use.
        ipam = HostLocalIpam(tmp_path)
        await ipam.allocate("172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"])  # dynamic .2
        with pytest.raises(StaticAddressUnavailable):
            await ipam.allocate(
                "172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"], requested="172.30.1.9"
            )

    async def test_the_gateway_cannot_be_requested(self, tmp_path: Path) -> None:
        ipam = HostLocalIpam(tmp_path)
        with pytest.raises(StaticAddressUnavailable):
            await ipam.allocate(
                "172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"], requested="172.30.1.1"
            )

    async def test_a_requested_address_outside_the_subnet_is_refused(self, tmp_path: Path) -> None:
        ipam = HostLocalIpam(tmp_path)
        with pytest.raises(StaticAddressUnavailable):
            await ipam.allocate(
                "172.30.1.0/24", "cid", "eth0", reserve=["172.30.1.1"], requested="10.0.0.5"
            )

    async def test_the_broadcast_address_cannot_be_requested(self, tmp_path: Path) -> None:
        # It is *in* the network but is not a host address — the dynamic path never hands it out.
        ipam = HostLocalIpam(tmp_path)
        with pytest.raises(StaticAddressUnavailable):
            await ipam.allocate(
                "172.30.1.0/26", "cid", "eth0", reserve=["172.30.1.1"], requested="172.30.1.63"
            )

    async def test_purge_subnet_drops_leaked_claims_so_the_block_can_be_reused(
        self, tmp_path: Path
    ) -> None:
        # A detach that never landed leaves a claim behind. Once the session's block is given back,
        # that claim must not fail the next session's kernel that is pinned at the same address.
        ipam = HostLocalIpam(tmp_path)
        await ipam.allocate(
            "172.30.1.0/24", "dead-kernel", "eth0", reserve=["172.30.1.1"], requested="172.30.1.2"
        )
        await ipam.purge_subnet("172.30.1.0/24")

        assert await ipam.owners("172.30.1.0/24") == {}
        assert (
            await ipam.allocate(
                "172.30.1.0/24",
                "new-kernel",
                "eth0",
                reserve=["172.30.1.1"],
                requested="172.30.1.2",
            )
            == "172.30.1.2"
        )


class TestHostLocalIpamJournal:
    async def test_allocation_survives_a_restart(self, tmp_path: Path) -> None:
        held = await HostLocalIpam(tmp_path).allocate(
            "172.30.1.0/24", "cidA", "eth0", reserve=["172.30.1.1"]
        )

        restarted = HostLocalIpam(tmp_path)  # fresh process, same on-disk journal
        assert (
            await restarted.allocate("172.30.1.0/24", "cidA", "eth0", reserve=["172.30.1.1"])
            == held
        )
        newcomer = await restarted.allocate("172.30.1.0/24", "cidB", "eth0", reserve=["172.30.1.1"])
        assert newcomer != held  # the survivor's address is not handed out again

    async def test_release_survives_a_restart(self, tmp_path: Path) -> None:
        held = await HostLocalIpam(tmp_path).allocate(
            "172.30.1.0/24", "cidA", "eth0", reserve=["172.30.1.1"]
        )
        await HostLocalIpam(tmp_path).release("172.30.1.0/24", "cidA", "eth0")
        reused = await HostLocalIpam(tmp_path).allocate(
            "172.30.1.0/24", "cidB", "eth0", reserve=["172.30.1.1"]
        )
        assert reused == held

    async def test_an_address_appearing_behind_the_owner_raises(self, tmp_path: Path) -> None:
        # The store has one writer per node; a record the owner believes free means a second one.
        ipam = HostLocalIpam(tmp_path)
        await ipam.allocate("172.30.1.0/24", "cidA", "eth0", reserve=["172.30.1.1"])

        subnet_dir = tmp_path / "172.30.1.0_24"
        (subnet_dir / "172.30.1.3").write_text("written-by-someone-else")

        with pytest.raises(NetworkStateStoreConflict):
            await ipam.allocate("172.30.1.0/24", "cidB", "eth0", reserve=["172.30.1.1"])
        assert (subnet_dir / "172.30.1.3").read_text() == "written-by-someone-else"


class TestHostLocalIpamOwnership:
    """Each agent builds its own NativeBridgeAttachRunner, but one node has one IP space: the
    runners must resolve the same IPAM or two agents would hand out the same address."""

    def test_one_ipam_per_store(self, tmp_path: Path) -> None:
        assert get_host_local_ipam(tmp_path) is get_host_local_ipam(tmp_path)

    def test_runners_over_one_store_share_an_ipam(self, tmp_path: Path) -> None:
        primary = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        auxiliary = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        assert primary._ipam is auxiliary._ipam

    async def test_concurrent_agents_never_share_an_address(self, tmp_path: Path) -> None:
        primary = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)._ipam
        auxiliary = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)._ipam

        ips = await asyncio.gather(
            primary.allocate("172.30.1.0/24", "cidA", "eth0", reserve=["172.30.1.1"]),
            auxiliary.allocate("172.30.1.0/24", "cidB", "eth0", reserve=["172.30.1.1"]),
        )
        assert len(set(ips)) == 2


class _RunRecorder:
    def __init__(
        self,
        existing: set[str] | None = None,
        *,
        in_netns: set[str] | None = None,
        fail_on: list[str] | None = None,
    ) -> None:
        self.calls: list[list[str]] = []
        self._existing = existing or set()  # interface names that "exist" in the HOST netns
        self._in_netns = in_netns or set()  # interface names that exist inside the CONTAINER netns
        self._fail_on = fail_on  # the argv prefix that raises, to drive a mid-attach failure

    async def __call__(self, argv: Any, *, check: bool = True) -> tuple[int, bytes, bytes]:
        argv = list(argv)
        self.calls.append(argv)
        if self._fail_on is not None and argv[: len(self._fail_on)] == self._fail_on:
            raise RuntimeError(f"command failed: {' '.join(argv)}")
        # emulate `nsenter --net=... -- ip link show <dev>` (the container side of the check)
        if argv[0] == "nsenter" and argv[3:6] == ["ip", "link", "show"]:
            return (0 if argv[6] in self._in_netns else 1), b"", b""
        # emulate `ip link show <dev>` / `iptables -C`: rc 0 if present, else 1
        if argv[:3] == ["ip", "link", "show"]:
            return (0 if argv[3] in self._existing else 1), b"", b""
        if argv[0] == "iptables" and "-C" in argv:
            return 1, b"", b""  # any rule-check reports absent -> triggers the add
        return 0, b"", b""

    def flat(self) -> str:
        return "\n".join(" ".join(c) for c in self.calls)


class TestNativeAttachStatic:
    async def test_add_static_returns_assigned_ip_and_wires_veth(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        rec = _RunRecorder(existing={"baimulti4097"})  # overlay bridge already exists
        monkeypatch.setattr(na, "_run", rec)
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        result = await runner(
            "ADD", ifname="baimulti0", netns=_NETNS, container_id="cid", config=_STATIC_CFG
        )
        assert result == {"ips": [{"address": "10.128.5.7/24"}]}
        flat = rec.flat()
        host = _veth_name("cid", "baimulti0", "h")
        assert f"ip link add {host} mtu 1450 type veth" in flat
        assert f"ip link set {host} master baimulti4097" in flat
        assert "nsenter --net=/proc/4242/ns/net -- ip addr add 10.128.5.7/24 dev baimulti0" in flat
        # static IPAM: no bridge gateway address, no MASQUERADE
        assert "addr replace" not in flat
        assert "MASQUERADE" not in flat
        # the overlay bridge's FORWARD-accept is the vxlan plugin's to own (at setup), not the
        # attacher's: an ipMasq=False attach must not touch FORWARD here.
        assert "-I FORWARD" not in flat
        # no mac in config -> the NIC keeps its kernel-assigned (random) address
        assert "link set baimulti0 address" not in flat

    async def test_add_static_pins_mac_when_config_carries_one(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        # Overlay endpoints carry a deterministic MAC (mac_for_ip); the NIC must own it,
        # set while down (before `up`), so peers' pre-programmed FDB/ARP resolves to it.
        rec = _RunRecorder(existing={"baimulti4097"})
        monkeypatch.setattr(na, "_run", rec)
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        await runner(
            "ADD",
            ifname="baimulti0",
            netns=_NETNS,
            container_id="cid",
            config={**_STATIC_CFG, "mac": "02:42:0a:80:05:07"},
        )
        flat = rec.flat()
        set_mac = (
            "nsenter --net=/proc/4242/ns/net -- ip link set baimulti0 address 02:42:0a:80:05:07"
        )
        assert set_mac in flat
        # MAC is applied before the link is brought up
        lines = flat.splitlines()
        assert lines.index(set_mac) < lines.index(
            "nsenter --net=/proc/4242/ns/net -- ip link set baimulti0 up"
        )


class TestNativeAttachLocal:
    async def test_add_local_sets_gateway_default_route_and_nat(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        rec = _RunRecorder(existing=set())  # local bridge must be created
        monkeypatch.setattr(na, "_run", rec)
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        result = await runner(
            "ADD", ifname="eth0", netns=_NETNS, container_id="cid", config=_LOCAL_CFG
        )
        assert result == {"ips": [{"address": "172.30.1.2/24"}]}
        flat = rec.flat()
        assert "ip link add bailo4097 type bridge" in flat
        assert "ip addr replace 172.30.1.1/24 dev bailo4097" in flat  # gateway on bridge
        assert "ip route replace default via 172.30.1.1" in flat
        assert (
            "iptables -t nat -A POSTROUTING -s 172.30.1.0/24 ! -d 172.30.1.0/24 -j MASQUERADE"
            in flat
        )
        # survive a DROP FORWARD policy (br_netfilter on a Docker/kube-proxy/hardened host):
        # accept traffic in and out of the LOCAL bridge, or egress + same-node ICC go silently dead.
        assert "iptables -I FORWARD -i bailo4097 -j ACCEPT" in flat
        assert "iptables -I FORWARD -o bailo4097 -j ACCEPT" in flat

    async def test_an_already_attached_container_is_a_noop(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        # A re-ADD (a retry, a restart) of a container that IS wired must not touch the wiring.
        host_veth = _veth_name("cid", "eth0", "h")
        rec = _RunRecorder(existing={"bailo4097", host_veth}, in_netns={"eth0"})
        monkeypatch.setattr(na, "_run", rec)
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)

        await runner("ADD", ifname="eth0", netns=_NETNS, container_id="cid", config=_LOCAL_CFG)

        assert "ip link add" not in rec.flat()
        assert f"ip link del {host_veth}" not in rec.flat()

    async def test_a_half_finished_attach_is_rebuilt_not_reported_as_success(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        # The host end exists but the container was never wired (its task died mid-ADD). Taking
        # that as "already attached" would return success for a container that comes up with NO
        # interface: its REPL never binds and its published ports DNAT to an address nobody owns.
        host_veth = _veth_name("cid", "eth0", "h")
        rec = _RunRecorder(existing={"bailo4097", host_veth}, in_netns=set())
        monkeypatch.setattr(na, "_run", rec)
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)

        result = await runner(
            "ADD", ifname="eth0", netns=_NETNS, container_id="cid", config=_LOCAL_CFG
        )

        flat = rec.flat()
        assert f"ip link del {host_veth}" in flat  # the leftover is cleared...
        assert f"ip link add {host_veth}" in flat  # ...and the container really wired
        assert result == {"ips": [{"address": "172.30.1.2/24"}]}

    async def test_a_failed_add_undoes_its_own_veth_and_address(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        # The caller's rollback covers the attachments that SUCCEEDED, not the one that raised —
        # and a veth pair whose peer never reached a netns is reaped by nothing. Clean up here.
        host_veth = _veth_name("cid", "eth0", "h")
        rec = _RunRecorder(
            existing={"bailo4097"},
            # the container's task dies between create_task and the attach
            fail_on=["ip", "link", "set", _veth_name("cid", "eth0", "c"), "netns"],
        )
        monkeypatch.setattr(na, "_run", rec)
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        ipam = get_host_local_ipam(tmp_path)  # the store that runner allocates from

        with pytest.raises(RuntimeError):
            await runner("ADD", ifname="eth0", netns=_NETNS, container_id="cid", config=_LOCAL_CFG)

        assert f"ip link del {host_veth}" in rec.flat()  # no veth left in the host namespace
        assert await ipam.owners("172.30.1.0/24") == {}  # and no address left claimed

    async def test_del_removes_veth_and_releases_ip(self, tmp_path: Path, monkeypatch: Any) -> None:
        rec = _RunRecorder(existing=set())
        monkeypatch.setattr(na, "_run", rec)
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        await runner("ADD", ifname="eth0", netns=_NETNS, container_id="cid", config=_LOCAL_CFG)
        await runner("DEL", ifname="eth0", netns=_NETNS, container_id="cid", config=_LOCAL_CFG)
        host = _veth_name("cid", "eth0", "h")
        assert f"ip link del {host}" in rec.flat()
        # the address is freed after DEL
        reused = await runner._ipam.allocate(
            "172.30.1.0/24", "other", "eth0", reserve=["172.30.1.1"]
        )
        assert reused == "172.30.1.2"

    async def test_del_last_owner_removes_forward_accept_with_masq(
        self, tmp_path: Path, monkeypatch: Any
    ) -> None:
        # The LOCAL bridge's FORWARD-accept shares the MASQUERADE lifecycle: torn down when the
        # last container on the subnet leaves, so a reused bridge name never inherits a stale rule.
        rec = _RunRecorder(existing=set())
        monkeypatch.setattr(na, "_run", rec)
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        await runner("ADD", ifname="eth0", netns=_NETNS, container_id="cid", config=_LOCAL_CFG)
        rec.calls.clear()
        await runner("DEL", ifname="eth0", netns=_NETNS, container_id="cid", config=_LOCAL_CFG)
        flat = rec.flat()
        assert "iptables -D FORWARD -i bailo4097 -j ACCEPT" in flat
        assert "iptables -D FORWARD -o bailo4097 -j ACCEPT" in flat
        assert "MASQUERADE" in flat  # removed alongside


class TestUnsupported:
    async def test_unknown_command_raises(self, tmp_path: Path, monkeypatch: Any) -> None:
        monkeypatch.setattr(na, "_run", _RunRecorder())
        runner = NativeBridgeAttachRunner(ipam_state_dir=tmp_path)
        with pytest.raises(ValueError):
            await runner("CHECK", ifname="eth0", netns=_NETNS, container_id="c", config=_LOCAL_CFG)
