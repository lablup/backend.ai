from __future__ import annotations

import asyncio
import uuid
from ipaddress import IPv4Address, IPv4Network

import pytest

from ai.backend.agent.containerd.network import KernelNetwork, PortForward, run_command
from ai.backend.agent.errors.containerd import (
    KernelAddressExhausted,
    KernelBridgeInvalid,
    KernelNetworkSetupFailed,
)
from ai.backend.common.types import KernelId

from .fakes import FakeCommandRunner


def _kid() -> KernelId:
    return KernelId(uuid.uuid4())


class TestInit:
    async def test_bridge_is_created_with_the_gateway_address(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        runner.script(["ip", "-d", "link", "show"], returncode=1)

        await network.init()

        assert runner.calls[:5] == [
            ("ip", "-d", "link", "show", "dev", "bai0"),
            ("ip", "link", "add", "bai0", "type", "bridge"),
            ("ip", "addr", "replace", "172.30.0.1/24", "dev", "bai0"),
            ("ip", "link", "set", "bai0", "up"),
            ("sysctl", "-n", "net.ipv4.ip_forward"),
        ]

    async def test_existing_bridge_is_kept_and_other_links_are_refused(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        runner.script(["ip", "-d", "link", "show"], "3: bai0: <UP>\n    bridge forward_delay 1\n")
        await network.init()
        assert runner.matching("ip", "link", "add") == []

        runner.script(["ip", "-d", "link", "show"], "2: bai0: <UP>\n    veth addrgenmode eui64\n")
        with pytest.raises(KernelBridgeInvalid):
            await network.init()


_IPT = ("iptables", "-w")


class TestInitRules:
    @pytest.fixture(autouse=True)
    def _bridge_exists(self, runner: FakeCommandRunner) -> None:
        runner.script(
            ["ip", "-d", "link", "show"], "3: bai0: <UP>\n    bridge forward_delay 1500\n"
        )

    async def test_chains_are_created_when_missing(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        runner.script([*_IPT, "-t", "nat", "-S", "bai0-DNAT"], returncode=1)
        runner.script([*_IPT, "-S", "bai0-FORWARD"], returncode=1)

        await network.init()

        assert runner.matching(*_IPT, "-t", "nat", "-N") == [
            (*_IPT, "-t", "nat", "-N", "bai0-DNAT")
        ]
        assert runner.matching(*_IPT, "-N") == [(*_IPT, "-N", "bai0-FORWARD")]

    async def test_missing_hooks_are_inserted_for_the_port_range(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        runner.script([*_IPT, "-t", "nat", "-C", "PREROUTING"], returncode=1)

        await network.init()

        assert runner.matching(*_IPT, "-t", "nat", "-I", "PREROUTING") == [
            (
                *_IPT,
                *("-t", "nat", "-I", "PREROUTING", "1", "-p", "tcp", "--dport", "30000:30999"),
                *("-m", "addrtype", "--dst-type", "LOCAL", "-j", "bai0-DNAT"),
            )
        ]
        assert runner.matching(*_IPT, "-I", "FORWARD") == []

    async def test_egress_masquerades_and_the_metadata_endpoint_is_rejected(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        await network.init()

        masq = runner.matching(*_IPT, "-t", "nat", "-A", "bai0-POSTROUTING")
        assert masq[0] == (
            *(*_IPT, "-t", "nat", "-A", "bai0-POSTROUTING"),
            *("-s", "172.30.0.0/24", "!", "-o", "bai0", "-j", "MASQUERADE"),
        )
        reject = ("-i", "bai0", "-d", "169.254.169.254/32", "-j", "REJECT")
        assert (*_IPT, "-A", "bai0-FORWARD", *reject) in runner.calls
        assert (*_IPT, "-A", "bai0-INPUT", *reject) in runner.calls
        assert runner.matching(*_IPT, "-A", "bai0-FORWARD")[-1][-2:] == ("-j", "DROP")

    async def test_hairpin_masquerade_covers_dnat_traffic_back_into_the_bridge(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        await network.init()

        hairpin = ("-s", "172.30.0.0/24", "-o", "bai0", "-m", "conntrack", "--ctstate", "DNAT")
        assert (*_IPT, "-t", "nat", "-A", "bai0-POSTROUTING", *hairpin, "-j", "MASQUERADE") in (
            runner.calls
        )

    async def test_existing_hooks_are_not_inserted_again(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        await network.init()

        assert runner.matching(*_IPT, "-I") == []
        assert runner.matching(*_IPT, "-t", "nat", "-I") == []

    async def test_stale_jump_of_an_older_config_is_deleted(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        stale = "-A POSTROUTING -s 10.9.0.0/24 -j bai0-POSTROUTING"
        runner.script(
            [*_IPT, "-t", "nat", "-S", "POSTROUTING"], f"-P POSTROUTING ACCEPT\n{stale}\n"
        )

        await network.init()

        assert runner.matching(*_IPT, "-t", "nat", "-D", "POSTROUTING") == [
            (*_IPT, "-t", "nat", "-D", "POSTROUTING", "-s", "10.9.0.0/24", "-j", "bai0-POSTROUTING")
        ]

    async def test_ip_forward_off_is_refused(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        runner.script(["sysctl", "-n", "net.ipv4.ip_forward"], "0\n")

        with pytest.raises(KernelNetworkSetupFailed, match="ip_forward"):
            await network.init()

        assert runner.matching(*_IPT) == []


class TestPublish:
    async def test_one_dnat_rule_per_forward_tagged_with_the_kernel(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        kid = _kid()
        await network.setup(kid)

        await network.publish(kid, [PortForward(30001, 8080), PortForward(30002, 22)])

        rule = (*_IPT, "-t", "nat", "-A", "bai0-DNAT", "-p", "tcp", "-d", "10.0.0.5/32")
        tail = ("-m", "comment", "--comment", f"bai-kernel={kid}", "-j", "DNAT")
        assert runner.matching(*_IPT, "-t", "nat", "-A", "bai0-DNAT") == [
            (*rule, "--dport", "30001", *tail, "--to-destination", "172.30.0.2:8080"),
            (*rule, "--dport", "30002", *tail, "--to-destination", "172.30.0.2:22"),
        ]

    async def test_stale_rule_on_the_same_host_port_is_deleted_first(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        kid = _kid()
        await network.setup(kid)
        old = "-A bai0-DNAT -p tcp --dport 30001 -m comment --comment bai-kernel=x -j DNAT"
        other = old.replace("30001", "30002")
        runner.script(
            [*_IPT, "-t", "nat", "-S", "bai0-DNAT"],
            f"-N bai0-DNAT\n{old} --to-destination 172.30.0.9:80\n{other} --to-destination 1.1.1.1:1\n",
        )

        await network.publish(kid, [PortForward(30001, 8080)])

        deleted = runner.matching(*_IPT, "-t", "nat", "-D", "bai0-DNAT")
        assert len(deleted) == 1 and "30001" in deleted[0]
        deleted_at = runner.calls.index(deleted[0])
        added_at = runner.calls.index(runner.matching(*_IPT, "-t", "nat", "-A", "bai0-DNAT")[0])
        assert deleted_at < added_at

    async def test_any_bind_host_adds_no_destination_match(self, runner: FakeCommandRunner) -> None:
        network = KernelNetwork(
            "bai0", IPv4Network("172.30.0.0/24"), "0.0.0.0", (30000, 30999), run=runner
        )
        kid = _kid()
        await network.setup(kid)

        await network.publish(kid, [PortForward(30001, 8080)])

        assert "-d" not in runner.matching(*_IPT, "-t", "nat", "-A", "bai0-DNAT")[0]

    async def test_publish_without_setup_raises(self, network: KernelNetwork) -> None:
        with pytest.raises(KernelNetworkSetupFailed, match="setup did not run"):
            await network.publish(_kid(), [PortForward(30001, 8080)])


class TestSetup:
    async def test_veth_pair_joins_the_bridge_and_the_netns(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        kid = _kid()
        ns, veth = f"bai0-{kid}", f"bai{kid.hex[:12]}"

        address = await network.setup(kid)

        assert address == IPv4Address("172.30.0.2")
        assert runner.calls == [
            ("ip", "netns", "add", ns),
            ("ip", "link", "add", veth, "type", "veth", "peer", "name", "eth0", "netns", ns),
            ("ip", "link", "set", veth, "master", "bai0"),
            ("ip", "link", "set", "dev", veth, "type", "bridge_slave", "isolated", "on"),
            ("ip", "link", "set", veth, "up"),
            ("ip", "-n", ns, "addr", "add", "172.30.0.2/24", "dev", "eth0"),
            ("ip", "-n", ns, "link", "set", "eth0", "up"),
            ("ip", "-n", ns, "link", "set", "lo", "up"),
            ("ip", "-n", ns, "route", "add", "default", "via", "172.30.0.1"),
        ]

    async def test_addresses_skip_the_gateway_and_released_ones_are_reused(
        self, network: KernelNetwork
    ) -> None:
        kid = _kid()
        assert await network.setup(kid) == IPv4Address("172.30.0.2")
        assert await network.setup(_kid()) == IPv4Address("172.30.0.3")

        await network.teardown(kid)

        assert await network.setup(_kid()) == IPv4Address("172.30.0.2")

    async def test_exhausted_subnet_raises(self, runner: FakeCommandRunner) -> None:
        network = KernelNetwork(
            "bai0", IPv4Network("172.30.0.0/30"), "0.0.0.0", (30000, 30999), run=runner
        )
        await network.setup(_kid())

        with pytest.raises(KernelAddressExhausted):
            await network.setup(_kid())


class TestTeardown:
    async def test_veth_and_netns_are_removed(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        kid = _kid()
        runner.script(["ip", "netns", "list"], f"bai0-{kid} (id: 3)\nother\n")

        await network.teardown(kid)

        assert runner.matching("ip", "link", "del") == [("ip", "link", "del", f"bai{kid.hex[:12]}")]
        assert runner.matching("ip", "netns", "del") == [("ip", "netns", "del", f"bai0-{kid}")]

    async def test_absent_pieces_are_skipped(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        runner.script(["ip", "link", "show"], returncode=1)

        await network.teardown(_kid())

        assert runner.matching("ip", "link", "del") == []
        assert runner.matching("ip", "netns", "del") == []


class TestDnatCleanup:
    async def test_teardown_deletes_only_the_kernels_rules(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        kid, other = _kid(), _kid()
        runner.script(
            [*_IPT, "-t", "nat", "-S", "bai0-DNAT"],
            "-N bai0-DNAT\n"
            f'-A bai0-DNAT -p tcp -m tcp --dport 30001 -m comment --comment "bai-kernel={kid}"'
            " -j DNAT --to-destination 172.30.0.2:8080\n"
            f'-A bai0-DNAT -p tcp -m tcp --dport 30002 -m comment --comment "bai-kernel={other}"'
            " -j DNAT --to-destination 172.30.0.3:8080\n",
        )

        await network.teardown(kid)

        deleted = runner.matching(*_IPT, "-t", "nat", "-D", "bai0-DNAT")
        assert len(deleted) == 1
        assert "30001" in deleted[0]

    async def test_sweep_removes_the_rules_of_a_kernel_without_a_netns(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        stale = _kid()
        runner.script(
            [*_IPT, "-t", "nat", "-S", "bai0-DNAT"],
            f'-A bai0-DNAT -p tcp -m tcp --dport 30001 -m comment --comment "bai-kernel={stale}"'
            " -j DNAT --to-destination 172.30.0.2:8080\n",
        )

        await network.sweep([])

        assert len(runner.matching(*_IPT, "-t", "nat", "-D", "bai0-DNAT")) == 1


class TestSweep:
    async def test_only_stale_netns_of_this_bridge_are_removed(
        self, network: KernelNetwork, runner: FakeCommandRunner
    ) -> None:
        alive, stale = _kid(), _kid()
        runner.script(
            ["ip", "netns", "list"],
            f"bai0-{alive}\nbai0-{stale}\nbai1-{_kid()}\nbai0-not-a-uuid\n",
        )

        await network.sweep([alive])

        assert runner.matching("ip", "netns", "del") == [("ip", "netns", "del", f"bai0-{stale}")]


class TestRunCommand:
    async def test_output_and_unchecked_exit_code_are_returned(self) -> None:
        assert (await run_command("echo", "hi")).stdout == "hi\n"
        assert (await run_command("sh", "-c", "exit 3", check=False)).returncode == 3

    @pytest.mark.parametrize(
        ("argv", "message"),
        [
            (("sh", "-c", "echo boom >&2; exit 3"), "boom"),
            (("bai-no-such-binary-xyz",), "cannot run"),
        ],
    )
    async def test_failure_raises(self, argv: tuple[str, ...], message: str) -> None:
        with pytest.raises(KernelNetworkSetupFailed, match=message):
            await run_command(*argv)

    async def test_timeout_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("ai.backend.agent.containerd.network._COMMAND_TIMEOUT_SEC", 0.2)

        with pytest.raises(KernelNetworkSetupFailed, match="timed out"):
            await run_command("sleep", "5")

    async def test_cancellation_propagates(self) -> None:
        task = asyncio.create_task(run_command("sleep", "30"))
        await asyncio.sleep(0.1)

        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
