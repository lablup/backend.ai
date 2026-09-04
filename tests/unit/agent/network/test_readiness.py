"""What `probe_readiness` reports, and why each finding is worth a session not being scheduled.

The parsing cases are pinned against real `ip -d link` output rather than an idealised form: the
one-line variant truncates before `dstport`, the JSON variant is malformed or empty depending on
the kernel, and the attribute line carries a bare `fan-map` token between the id and the rest.
"""

from __future__ import annotations

from ai.backend.agent.network.readiness import (
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
