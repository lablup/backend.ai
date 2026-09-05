"""What `probe_readiness` reports, and why each finding is worth a session not being scheduled.

The parsing cases are pinned against real `ip -d link` output rather than an idealised form: the
one-line variant truncates before `dstport`, the JSON variant is malformed or empty depending on
the kernel, and the attribute line carries a bare `fan-map` token between the id and the rest.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.agent.network.backends import vxlan
from ai.backend.agent.network.caps import compute_caps
from ai.backend.agent.network.readiness import (
    Readiness,
    VxlanDevice,
    foreign_conflicts,
    parse_vxlan_details,
)

_TWO_DEVICES = """\
4: vxA: <BROADCAST,MULTICAST> mtu 1450 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 06:7a:b6:c6:6a:9d brd ff:ff:ff:ff:ff:ff promiscuity 0  allmulti 0 minmtu 68
    vxlan id 4097 fan-map dev dummy0 srcport 0 0 dstport 4789 ttl auto ageing 300 udpcsum
5: vxB: <BROADCAST,MULTICAST> mtu 1450 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 0a:f0:91:07:5d:c9 brd ff:ff:ff:ff:ff:ff promiscuity 0  allmulti 0 minmtu 68
    vxlan id 900 dev dummy0 srcport 0 0 dstport 8472 ttl auto ageing 300 udpcsum
"""

_OURS = """\
7: baivx4096@enp4s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue master baibr4096
    link/ether 12:34:56:78:9a:bc brd ff:ff:ff:ff:ff:ff promiscuity 1  allmulti 0 minmtu 68
    vxlan id 4096 local 192.168.0.104 dev enp4s0 srcport 0 0 dstport 4789 ttl auto ageing 300
"""


class TestParsingVxlanDetails:
    def test_it_reads_the_vni_and_the_port(self) -> None:
        devices = parse_vxlan_details(_TWO_DEVICES)
        assert {(d.name, d.vni, d.dstport) for d in devices} == {
            ("vxA", 4097, 4789),
            ("vxB", 900, 8472),
        }

    def test_a_fan_map_token_between_the_id_and_the_rest_is_tolerated(self) -> None:
        # The same token that makes `ip -d -j link` emit malformed JSON on 6.14.
        (device,) = [d for d in parse_vxlan_details(_TWO_DEVICES) if d.name == "vxA"]
        assert device.dstport == 4789

    def test_our_own_device_is_recognised(self) -> None:
        (device,) = parse_vxlan_details(_OURS)
        assert device.is_ours is True
        assert device.name == "baivx4096"

    def test_empty_output_is_no_devices(self) -> None:
        assert parse_vxlan_details("") == ()


class TestForeignConflicts:
    """The drop and mark rules select on (UDP port, VNI) and nothing else, so a co-tenant on our
    port with a VNI in our range has its frames marked for our XFRM policy, or dropped as
    unprotected plaintext."""

    def test_same_port_and_a_vni_in_range_is_reported(self) -> None:
        found = foreign_conflicts(
            [VxlanDevice("flannel.1", 4097, 4789)], port=4789, vni_range=(4096, 16777215)
        )
        assert len(found) == 1
        assert "flannel.1" in found[0]

    def test_same_port_outside_the_range_is_reported_as_not_yet_colliding(self) -> None:
        found = foreign_conflicts(
            [VxlanDevice("flannel.1", 1, 4789)], port=4789, vni_range=(4096, 16777215)
        )
        assert len(found) == 1
        assert "outside" in found[0]

    def test_a_different_port_is_not_a_conflict(self) -> None:
        # Moving either side off the shared port is the fix, so a tunnel that already did is fine
        # however its VNI is numbered.
        assert (
            foreign_conflicts(
                [VxlanDevice("flannel.1", 4097, 8472)], port=4789, vni_range=(4096, 16777215)
            )
            == []
        )

    def test_our_own_devices_are_not_conflicts(self) -> None:
        assert (
            foreign_conflicts(
                [VxlanDevice("baivx4096", 4096, 4789)], port=4789, vni_range=(4096, 16777215)
            )
            == []
        )


class TestReadinessGatesTheAdvertisedBackend:
    """Reporting a problem is not enough on its own: the manager selects on `backends`, so a node
    that keeps advertising `vxlan` keeps being handed sessions that can only fail on it."""

    def test_a_node_missing_its_tooling_stops_advertising_vxlan(self) -> None:
        caps = compute_caps(
            tunnel_offload=False,
            readiness=Readiness(blocking=("iptables has no `u32` match",)),
        )
        assert caps.backends == []
        assert caps.readiness == ["iptables has no `u32` match"]

    def test_an_advisory_conflict_does_not_take_the_node_out(self) -> None:
        # Whether it actually collides depends on which VNI a session draws, and the exact
        # collision is refused at setup where both are known.
        caps = compute_caps(
            tunnel_offload=False,
            readiness=Readiness(advisory=("flannel.1 shares udp/4789",)),
        )
        assert caps.backends == ["vxlan"]
        assert caps.readiness == ["flannel.1 shares udp/4789"]

    def test_a_ready_node_advertises_normally(self) -> None:
        caps = compute_caps(tunnel_offload=True, readiness=Readiness())
        assert caps.backends == ["vxlan"]
        assert caps.readiness == []


class TestUnreadableDevicesAreNotSilence:
    """`ip -d` is not dependable on every host, and its failure is not a clean error: on three
    hosts running the same iproute2 6.1.0 it SEGFAULTS, in opposite directions. Reporting "no
    conflict" because the host could not be asked is the fail-open this check exists to remove."""

    def test_an_unparseable_listing_yields_no_devices(self) -> None:
        assert parse_vxlan_details("Segmentation fault") == ()

    def test_a_conflict_is_still_found_in_a_partial_listing(self) -> None:
        # The per-device fallback describes what it can; whatever it cannot is reported separately.
        found = foreign_conflicts(
            [VxlanDevice("flannel.1", 4097, 4789)], port=4789, vni_range=(4096, 16777215)
        )
        assert len(found) == 1


class TestWhetherThisNodeCanEncryptAtAll:
    """The generic checks -- ip, bridge, iptables, u32 -- say nothing about ESP, so the answer is
    found by TRYING: the overlay's real SA and outbound policy are installed on documentation
    addresses, read back, and removed.

    Reading /proc instead was wrong twice over: `xfrm_stat` is CONFIG_XFRM_STATISTICS, which is
    neither necessary nor sufficient for the CONFIG_XFRM_USER interface `ip xfrm` needs, and a
    name in /proc/crypto is neither necessary (the crypto API loads a module on first use) nor
    sufficient (the listing carries internal `__`-prefixed implementations)."""

    def _probe(self, rec: Any, listing: tuple[str, str]) -> Any:
        state, policy = listing

        async def _reader(argv: Sequence[str]) -> str:
            return policy if list(argv[:3]) == ["ip", "xfrm", "policy"] else state

        return vxlan.probe_encryption_support(rec, _reader)

    async def test_a_kernel_that_installs_and_reports_it_back_can(self) -> None:
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))

        assert await self._probe(_runner, _installed()) == []
        assert any(c[:4] == ["ip", "xfrm", "state", "add"] for c in calls)
        assert any(c[:4] == ["ip", "xfrm", "policy", "update"] for c in calls)

    async def test_a_kernel_that_refuses_the_state_cannot(self) -> None:
        async def _runner(argv: Sequence[str]) -> None:
            if argv[:4] == ["ip", "xfrm", "state", "add"]:
                raise RuntimeError("RTNETLINK answers: Operation not supported")

        problems = await self._probe(_runner, ("", ""))
        assert any("cannot install" in p for p in problems)

    async def test_a_kernel_that_accepts_but_does_not_report_esn_cannot(self) -> None:
        # It accepts the SA and then holds something weaker. Only reading it back finds that.
        async def _runner(argv: Sequence[str]) -> None:
            return None

        problems = await self._probe(_runner, _installed(esn=False))
        assert any("ESN" in p for p in problems)

    async def test_a_kernel_that_loses_the_policy_cannot(self) -> None:
        async def _runner(argv: Sequence[str]) -> None:
            return None

        problems = await self._probe(_runner, _installed(policy=False))
        assert any("policy" in p for p in problems)

    async def test_the_probe_cleans_up_after_itself(self) -> None:
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))

        await self._probe(_runner, _installed())
        assert any(c[:4] == ["ip", "xfrm", "state", "del"] for c in calls)
        assert any(c[:4] == ["ip", "xfrm", "policy", "del"] for c in calls)

    async def test_it_cleans_up_after_a_failure_too(self) -> None:
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))
            if argv[:4] == ["ip", "xfrm", "policy", "update"]:
                raise RuntimeError("no")

        await self._probe(_runner, ("", ""))
        assert any(c[:4] == ["ip", "xfrm", "state", "del"] for c in calls)

    async def test_it_only_ever_touches_documentation_addresses(self) -> None:
        # A leftover after a crash must select nothing real. TEST-NET-1 is never routed and never
        # a VTEP.
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))

        await self._probe(_runner, _installed())
        addresses = {c[i + 1] for c in calls for i, t in enumerate(c) if t in ("src", "dst")}
        assert addresses <= {"192.0.2.1", "192.0.2.2", "192.0.2.1/32", "192.0.2.2/32"}

    def test_the_two_answers_are_separate(self) -> None:
        # A cluster may legitimately run unencrypted on a kernel with no ESP, so "cannot encrypt"
        # must not read as "cannot serve the overlay".
        findings = Readiness(encryption_blocking=("this node cannot install the ESP state",))
        assert findings.can_serve_overlay is True
        assert findings.can_encrypt_overlay is False

    def test_a_node_that_cannot_serve_cannot_encrypt_either(self) -> None:
        findings = Readiness(blocking=("iptables has no `u32` match",))
        assert findings.can_encrypt_overlay is False

    def test_the_reason_is_published(self) -> None:
        findings = Readiness(encryption_blocking=("this node cannot install the ESP state",))
        assert "this node cannot install the ESP state" in findings.problems


def _installed(*, esn: bool = True, policy: bool = True) -> tuple[str, str]:
    """`(ip xfrm state, ip xfrm policy)` output for a probe the kernel accepted as asked."""
    spi = vxlan._esp_spi("192.0.2.1", "192.0.2.2")
    state = (
        "src 192.0.2.1 dst 192.0.2.2\n"
        f"\tproto esp spi {spi:#x} reqid {vxlan.XFRM_REQID} mode transport\n"
        + ("\treplay-window 0 flag esn\n" if esn else "\treplay-window 0\n")
        + "\taead rfc4106(gcm(aes)) 0xdeadbeef 128\n"
    )
    rule = (
        "src 192.0.2.1/32 dst 192.0.2.2/32 proto udp dport 4789 \n"
        "\tdir out priority 0 \n"
        f"\tmark {vxlan.XFRM_MARK:#x}/0xffffffff \n"
        f"\ttmpl src 192.0.2.1 dst 192.0.2.2 proto esp spi {spi:#x}"
        f" reqid {vxlan.XFRM_REQID} mode transport\n"
    )
    return state, (rule if policy else "")
