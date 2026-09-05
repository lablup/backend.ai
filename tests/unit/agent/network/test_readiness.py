"""What `probe_readiness` reports, and why each finding is worth a session not being scheduled.

The parsing cases are pinned against real `ip -d link` output rather than an idealised form: the
one-line variant truncates before `dstport`, the JSON variant is malformed or empty depending on
the kernel, and the attribute line carries a bare `fan-map` token between the id and the rest.
"""

from __future__ import annotations

import os
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
    found by TRYING: the overlay's real SA pair and outbound policy are installed, read back, and
    thrown away with the namespace they were made in.

    Reading /proc instead was wrong twice over: `xfrm_stat` is CONFIG_XFRM_STATISTICS, which is
    neither necessary nor sufficient for the CONFIG_XFRM_USER interface `ip xfrm` needs, and a
    name in /proc/crypto is neither necessary (the crypto API loads a module on first use) nor
    sufficient (the listing carries internal `__`-prefixed implementations)."""

    def _probe(self, runner: Any, listing: tuple[str, str], netns: str = "") -> Any:
        state, policy = listing

        async def _reader(argv: Sequence[str]) -> str:
            if list(argv[:3]) == ["ip", "netns", "list"]:
                return netns
            return policy if argv[-1] == "policy" else state

        return vxlan.probe_encryption_support(runner, _reader)

    async def test_a_kernel_that_installs_and_reports_it_back_can(self) -> None:
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))

        assert await self._probe(_runner, _installed()) == []
        assert any(c[:3] == ["ip", "netns", "add"] for c in calls)
        assert any("state" in c and "add" in c for c in calls)
        assert any("policy" in c and "update" in c for c in calls)

    async def test_a_node_that_cannot_make_a_namespace_says_so(self) -> None:
        async def _runner(argv: Sequence[str]) -> None:
            if argv[:3] == ["ip", "netns", "add"]:
                raise RuntimeError("Operation not permitted")

        problems = await self._probe(_runner, ("", ""))
        assert any("network namespace" in p for p in problems)

    async def test_a_kernel_that_refuses_the_state_cannot(self) -> None:
        async def _runner(argv: Sequence[str]) -> None:
            if "state" in argv and "add" in argv:
                raise RuntimeError("RTNETLINK answers: Operation not supported")

        problems = await self._probe(_runner, ("", ""))
        assert any("cannot install" in p for p in problems)

    async def test_a_kernel_that_accepts_but_does_not_report_esn_cannot(self) -> None:
        # It accepts the SA and then holds something weaker. Only reading it back finds that.
        async def _runner(argv: Sequence[str]) -> None:
            return None

        problems = await self._probe(_runner, _installed(esn=False))
        assert any("ESN" in p for p in problems)

    async def test_only_one_direction_installed_is_not_enough(self) -> None:
        # A session installs an outbound SA and an inbound one. A kernel that took the first is
        # not thereby known to have taken the second.
        async def _runner(argv: Sequence[str]) -> None:
            return None

        problems = await self._probe(_runner, _installed(inbound=False))
        assert any("192.0.2.2 -> 192.0.2.1" in p for p in problems)

    async def test_a_policy_of_some_other_session_does_not_count(self) -> None:
        # "Some policy of ours exists" passes on any host already running a session, which is
        # every host this matters on.
        async def _runner(argv: Sequence[str]) -> None:
            return None

        problems = await self._probe(_runner, _installed(policy="elsewhere"))
        assert any("outbound ESP policy" in p for p in problems)

    async def test_a_policy_selecting_the_wrong_sa_does_not_count(self) -> None:
        async def _runner(argv: Sequence[str]) -> None:
            return None

        problems = await self._probe(_runner, _installed(policy="wrong-spi"))
        assert any("selecting the SA it was given" in p for p in problems)

    async def test_the_namespace_goes_afterwards(self) -> None:
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))

        await self._probe(_runner, _installed())
        assert any(c[:3] == ["ip", "netns", "del"] for c in calls)

    async def test_the_namespace_goes_after_a_failure_too(self) -> None:
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))
            if "policy" in argv and "update" in argv:
                raise RuntimeError("no")

        await self._probe(_runner, ("", ""))
        assert any(c[:3] == ["ip", "netns", "del"] for c in calls)

    async def test_a_namespace_that_will_not_go_does_not_change_this_answer(self) -> None:
        # The question asked was whether this node can encrypt, and it found that out. The leak is
        # the NEXT probe's to report -- see `TestReapingProbeNamespaces`.
        async def _runner(argv: Sequence[str]) -> None:
            if argv[:3] == ["ip", "netns", "del"]:
                raise RuntimeError("busy")

        assert await self._probe(_runner, _installed()) == []

    async def test_it_touches_nothing_outside_its_namespace(self) -> None:
        """The bug this shape exists for. Run in the host's namespace, the probe installed real
        XFRM objects at addresses nothing forbids a cluster from using as VTEPs -- and its cleanup
        deleted them by name, without checking it had created them, every sixty seconds."""
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))

        await self._probe(_runner, _installed())
        for call in calls:
            if call[:2] == ["ip", "netns"]:
                continue
            assert call[:2] == ["ip", "-n"], f"{call} ran in the host's namespace"
            assert call[2].startswith("bai-encprobe-")

    async def test_two_probes_do_not_share_a_namespace(self) -> None:
        names: list[str] = []

        async def _runner(argv: Sequence[str]) -> None:
            if argv[:3] == ["ip", "netns", "add"]:
                names.append(argv[3])

        await self._probe(_runner, _installed())
        await self._probe(_runner, _installed())
        assert len(set(names)) == 2

    async def test_no_deletes_are_issued_for_objects_it_may_not_have_made(self) -> None:
        # The namespace goes; the objects in it go with it. Deleting them by name is what reached
        # into a live session's state.
        calls: list[list[str]] = []

        async def _runner(argv: Sequence[str]) -> None:
            calls.append(list(argv))

        await self._probe(_runner, _installed())
        assert not any("del" in c and ("state" in c or "policy" in c) for c in calls)

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


def _installed(*, esn: bool = True, inbound: bool = True, policy: str = "probe") -> tuple[str, str]:
    """`(ip xfrm state, ip xfrm policy)` output for a probe the kernel accepted as asked.

    ``policy``: "probe" for the probe's own, "elsewhere" for another session's, "wrong-spi" for
    one that selects an SA the probe did not install, "" for none.
    """

    def _sa(src: str, dst: str, with_esn: bool) -> str:
        return (
            f"src {src} dst {dst}\n"
            f"\tproto esp spi {vxlan._esp_spi(src, dst):#x} reqid {vxlan.XFRM_REQID}"
            " mode transport\n"
            + ("\treplay-window 0 flag esn\n" if with_esn else "\treplay-window 0\n")
            + "\taead rfc4106(gcm(aes)) 0xdeadbeef 128\n"
        )

    state = _sa("192.0.2.1", "192.0.2.2", esn)
    if inbound:
        state += _sa("192.0.2.2", "192.0.2.1", esn)

    def _policy(src: str, dst: str, spi: int) -> str:
        return (
            f"src {src}/32 dst {dst}/32 proto udp dport 4789 \n"
            "\tdir out priority 0 \n"
            f"\tmark {vxlan.XFRM_MARK:#x}/0xffffffff \n"
            f"\ttmpl src {src} dst {dst} proto esp spi {spi:#x}"
            f" reqid {vxlan.XFRM_REQID} mode transport\n"
        )

    rules = {
        "probe": _policy("192.0.2.1", "192.0.2.2", vxlan._esp_spi("192.0.2.1", "192.0.2.2")),
        "elsewhere": _policy("10.0.0.1", "10.0.0.2", vxlan._esp_spi("10.0.0.1", "10.0.0.2")),
        "wrong-spi": _policy("192.0.2.1", "192.0.2.2", 0x1234),
        "": "",
    }
    return state, rules[policy]


class TestReapingProbeNamespaces:
    """A probe runs every time capabilities are refreshed -- once a minute on a busy agent -- so a
    removal that keeps failing, or a SIGKILL between creating a namespace and removing it,
    accumulates them for as long as the node runs. Nothing came back for them."""

    def _probe(self, runner: Any, netns_list: str) -> Any:
        async def _reader(argv: Sequence[str]) -> str:
            if list(argv[:3]) == ["ip", "netns", "list"]:
                return netns_list
            state, policy = _installed()
            return policy if argv[-1] == "policy" else state

        return vxlan.probe_encryption_support(runner, _reader)

    async def _deletions(self, netns_list: str) -> list[str]:
        """The namespaces this probe REAPED, without the one it made for itself."""
        deleted: list[str] = []
        made: list[str] = []

        async def _runner(argv: Sequence[str]) -> None:
            if list(argv[:3]) == ["ip", "netns", "add"]:
                made.append(argv[3])
            if list(argv[:3]) == ["ip", "netns", "del"]:
                deleted.append(argv[3])

        await self._probe(_runner, netns_list)
        return [name for name in deleted if name not in made]

    async def test_a_dead_processes_namespace_is_reaped(self) -> None:
        # pid 1 is alive; a pid that is not is what a killed agent leaves behind.
        dead = _free_pid()
        deleted = await self._deletions(f"bai-encprobe-{dead}-abcd (id: 3)\n")
        assert f"bai-encprobe-{dead}-abcd" in deleted

    async def test_a_live_co_located_agents_namespace_is_left(self) -> None:
        # Its probe is running right now; reaping it would break that agent's answer.
        deleted = await self._deletions("bai-encprobe-1-abcd (id: 3)\n")
        assert "bai-encprobe-1-abcd" not in deleted

    async def test_our_own_leftovers_are_reaped(self) -> None:
        # `_probe_lock` means no other probe of this process is running, so anything of ours is
        # finished with.
        mine = f"bai-encprobe-{os.getpid()}-abcd"
        assert mine in await self._deletions(f"{mine}\n")

    async def test_a_namespace_from_before_the_pid_was_in_the_name_is_reaped(self) -> None:
        assert "bai-encprobe-abcd" in await self._deletions("bai-encprobe-abcd\n")

    async def test_nothing_else_is_touched(self) -> None:
        listing = "bai-encprobe-1-live\ncni-1234\nsomeone-elses-netns (id: 0)\n"
        deleted = await self._deletions(listing)
        assert deleted == [], "it reaped a namespace that is not a probe's"

    async def test_one_that_will_not_go_is_reported(self) -> None:
        dead = _free_pid()

        async def _runner(argv: Sequence[str]) -> None:
            if list(argv[:3]) == ["ip", "netns", "del"] and argv[3].endswith("-abcd"):
                raise RuntimeError("Device or resource busy")

        problems = await self._probe(_runner, f"bai-encprobe-{dead}-abcd\n")
        assert any("leftover encryption probe namespace" in p for p in problems)

    async def test_an_unlistable_namespace_set_does_not_stop_the_probe(self) -> None:
        # Not knowing what is lying around is no reason to refuse to answer the question asked.
        async def _runner(argv: Sequence[str]) -> None:
            return None

        async def _reader(argv: Sequence[str]) -> str:
            if list(argv[:3]) == ["ip", "netns", "list"]:
                raise RuntimeError("no")
            state, policy = _installed()
            return policy if argv[-1] == "policy" else state

        assert await vxlan.probe_encryption_support(_runner, _reader) == []

    async def test_the_name_carries_this_process(self) -> None:
        made: list[str] = []

        async def _runner(argv: Sequence[str]) -> None:
            if list(argv[:3]) == ["ip", "netns", "add"]:
                made.append(argv[3])

        await self._probe(_runner, "")
        assert made and made[0].startswith(f"bai-encprobe-{os.getpid()}-")


def _free_pid() -> int:
    """A pid no process holds, for standing in as a killed agent's."""
    for candidate in range(4_000_000, 4_000_100):
        try:
            os.kill(candidate, 0)
        except ProcessLookupError:
            return candidate
        except OSError:
            continue
    raise AssertionError("no free pid to test with")
