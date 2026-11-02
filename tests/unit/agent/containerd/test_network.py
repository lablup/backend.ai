from __future__ import annotations

import asyncio
import uuid
from ipaddress import IPv4Address, IPv4Network

import psutil
import pytest

from ai.backend.agent.containerd.network import KernelNetwork, PortForward, run_command
from ai.backend.agent.errors.containerd import KernelAddressExhausted, KernelNetworkSetupFailed
from ai.backend.common.types import KernelId

from .fakes import FakeCommandRunner

BR = "bai-t"
SUBNET = IPv4Network("172.30.9.0/24")
PORT_RANGE = (30000, 31000)


def _kid() -> KernelId:
    return KernelId(uuid.uuid4())


def _network(
    runner: FakeCommandRunner, *, bind_host: str = "", subnet: IPv4Network = SUBNET
) -> KernelNetwork:
    return KernelNetwork(BR, subnet, bind_host, PORT_RANGE, run=runner)


def _hooks(runner: FakeCommandRunner) -> list[tuple[str, ...]]:
    """Each hook insertion as (table, chain, *rule)."""
    hooks: list[tuple[str, ...]] = []
    for call in runner.calls:
        if "-I" in call:
            table = call[3] if call[2] == "-t" else "filter"
            hooks.append((table, call[call.index("-I") + 1], *call[call.index("-I") + 3 :]))
    return hooks


def _present(runner: FakeCommandRunner) -> None:
    """Everything init() looks for already exists."""
    runner.script(["sysctl", "-n"], "1\n")


def _absent(runner: FakeCommandRunner) -> None:
    runner.script(["ip", "link", "show"], returncode=1)
    runner.script(["sysctl", "-n"], "1\n")
    runner.script(["iptables", "-w", "-t", "nat", "-S"], returncode=1)
    runner.script(["iptables", "-w", "-S"], returncode=1)
    runner.script(["iptables", "-w", "-t", "nat", "-C"], returncode=1)
    runner.script(["iptables", "-w", "-C"], returncode=1)


_FORWARD_WITH_BOTH_JUMPS = (
    "-P FORWARD ACCEPT\n"
    f"-A FORWARD -o {BR} -j {BR}-FORWARD\n"
    f"-A FORWARD -i {BR} -j {BR}-FORWARD\n"
    "-A FORWARD -j DOCKER-USER\n"
)


class TestInit:
    async def test_egress_rules_are_installed(self) -> None:
        runner = FakeCommandRunner()
        _absent(runner)

        await _network(runner).init()

        assert ("ip", "addr", "replace", "172.30.9.1/24", "dev", BR) in runner.calls
        masquerade: tuple[str, ...] = ("iptables", "-w", "-t", "nat", "-A", f"{BR}-POSTROUTING")
        masquerade += ("-s", "172.30.9.0/24", "!", "-o", BR, "-j", "MASQUERADE")
        assert masquerade in runner.calls
        accept = ("iptables", "-w", "-A", f"{BR}-FORWARD", "-i", BR, "!", "-o", BR, "-j", "ACCEPT")
        assert accept in runner.calls
        assert ("iptables", "-w", "-A", f"{BR}-FORWARD", "-o", BR, "-j", "DROP") in runner.calls

    async def test_metadata_address_is_rejected_from_the_bridge(self) -> None:
        runner = FakeCommandRunner()
        _absent(runner)

        await _network(runner).init()

        for chain in (f"{BR}-FORWARD", f"{BR}-INPUT"):
            reject: tuple[str, ...] = ("iptables", "-w", "-A", chain, "-i", BR)
            reject += ("-d", "169.254.169.254/32", "-j", "REJECT")
            assert reject in runner.calls
        forward = [c for c in runner.calls if c[:4] == ("iptables", "-w", "-A", f"{BR}-FORWARD")]
        assert forward[0][-2:] == ("-j", "REJECT")  # ahead of the egress accept

    async def test_ip_forward_off_stops_the_agent_without_writing_it(self) -> None:
        runner = FakeCommandRunner()
        runner.script(["sysctl", "-n"], "0\n")

        with pytest.raises(KernelNetworkSetupFailed, match="ip_forward"):
            await _network(runner).init()

        assert runner.matching("sysctl", "-w") == []
        assert runner.matching("iptables") == []

    async def test_foreign_chains_are_never_flushed(self) -> None:
        runner = FakeCommandRunner()
        _absent(runner)

        await _network(runner).init()

        flushed = [c[-1] for c in runner.calls if "-F" in c]
        assert all(chain.startswith(f"{BR}-") for chain in flushed)
        inserted = [c for c in runner.calls if "-I" in c]
        assert all(c[-1].startswith(f"{BR}-") for c in inserted)

    async def test_missing_pieces_are_created(self) -> None:
        runner = FakeCommandRunner()
        _absent(runner)

        await _network(runner).init()

        assert ("ip", "link", "add", BR, "type", "bridge") in runner.calls
        assert ("ip", "link", "set", BR, "up") in runner.calls
        created = [c[-1] for c in runner.matching("iptables", "-w") if "-N" in c]
        assert created == [f"{BR}-DNAT", f"{BR}-POSTROUTING", f"{BR}-FORWARD", f"{BR}-INPUT"]
        assert len(_hooks(runner)) == 6
        assert all(c[c.index("-I") + 2] == "1" for c in runner.calls if "-I" in c)

    async def test_hooks_are_scoped_to_the_bridge_subnet_and_port_range(self) -> None:
        runner = FakeCommandRunner()
        _absent(runner)

        await _network(runner).init()

        local = ("-p", "tcp", "--dport", "30000:31000", "-m", "addrtype", "--dst-type", "LOCAL")
        assert _hooks(runner) == [
            ("nat", "PREROUTING", *local, "-j", f"{BR}-DNAT"),
            ("nat", "OUTPUT", "!", "-d", "127.0.0.0/8", *local, "-j", f"{BR}-DNAT"),
            ("nat", "POSTROUTING", "-s", "172.30.9.0/24", "-j", f"{BR}-POSTROUTING"),
            ("filter", "FORWARD", "-i", BR, "-j", f"{BR}-FORWARD"),
            ("filter", "FORWARD", "-o", BR, "-j", f"{BR}-FORWARD"),
            ("filter", "INPUT", "-i", BR, "-j", f"{BR}-INPUT"),
        ]

    async def test_stale_jumps_to_our_chains_are_deleted_and_foreign_ones_kept(self) -> None:
        runner = FakeCommandRunner()
        _present(runner)
        runner.script(
            ["iptables", "-w", "-t", "nat", "-S", "POSTROUTING"],
            "-P POSTROUTING ACCEPT\n"
            f"-A POSTROUTING -s 172.30.8.0/24 -j {BR}-POSTROUTING\n"
            f"-A POSTROUTING -s 172.30.9.0/24 -j {BR}-POSTROUTING\n"
            "-A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE\n"
            "-A POSTROUTING -j DOCKER\n",
        )
        runner.script(
            ["iptables", "-w", "-t", "nat", "-S", "PREROUTING"],
            f"-A PREROUTING -p tcp -m tcp --dport 20000:21000 -m addrtype --dst-type LOCAL"
            f" -j {BR}-DNAT\n"
            f"-A PREROUTING -p tcp -m tcp --dport 30000:31000 -m addrtype --dst-type LOCAL"
            f" -j {BR}-DNAT\n"
            "-A PREROUTING -m addrtype --dst-type LOCAL -j DOCKER\n",
        )

        await _network(runner).init()

        deleted = [c for c in runner.calls if "-D" in c]
        assert deleted == [
            ("iptables", "-w", "-t", "nat", "-D", "PREROUTING", "-p", "tcp", "-m", "tcp")
            + ("--dport", "20000:21000", "-m", "addrtype", "--dst-type", "LOCAL")
            + ("-j", f"{BR}-DNAT"),
            ("iptables", "-w", "-t", "nat", "-D", "POSTROUTING", "-s", "172.30.8.0/24")
            + ("-j", f"{BR}-POSTROUTING"),
        ]

    async def test_both_forward_jumps_are_added_when_neither_exists(self) -> None:
        runner = FakeCommandRunner()
        _absent(runner)

        await _network(runner).init()

        forward = [h[2:] for h in _hooks(runner) if h[:2] == ("filter", "FORWARD")]
        assert forward == [("-i", BR, "-j", f"{BR}-FORWARD"), ("-o", BR, "-j", f"{BR}-FORWARD")]
        assert [c for c in runner.calls if "-D" in c] == []

    async def test_both_forward_jumps_survive_when_both_exist(self) -> None:
        runner = FakeCommandRunner()
        _present(runner)
        runner.script(["iptables", "-w", "-S", "FORWARD"], _FORWARD_WITH_BOTH_JUMPS)

        await _network(runner).init()

        assert [c for c in runner.calls if "-D" in c or "-I" in c] == []

    async def test_a_stale_forward_jump_is_removed_and_both_wanted_ones_are_kept(self) -> None:
        runner = FakeCommandRunner()
        _present(runner)
        runner.script(
            ["iptables", "-w", "-S", "FORWARD"],
            _FORWARD_WITH_BOTH_JUMPS + f"-A FORWARD -i bai-old -j {BR}-FORWARD\n",
        )

        await _network(runner).init()

        deleted = [c for c in runner.calls if "-D" in c]
        assert deleted == [
            ("iptables", "-w", "-D", "FORWARD", "-i", "bai-old", "-j", f"{BR}-FORWARD")
        ]
        assert [c for c in runner.calls if "-I" in c] == []

    async def test_init_twice_changes_nothing_the_second_time(self) -> None:
        runner = FakeCommandRunner()
        _present(runner)
        runner.script(["iptables", "-w", "-S", "FORWARD"], _FORWARD_WITH_BOTH_JUMPS)
        network = _network(runner)

        await network.init()
        first = len(runner.calls)
        await network.init()

        assert runner.calls[first:] == runner.calls[:first]
        assert [c for c in runner.calls if "-D" in c or "-I" in c] == []

    async def test_existing_pieces_are_left_alone(self) -> None:
        runner = FakeCommandRunner()
        _present(runner)

        await _network(runner).init()

        assert runner.matching("ip", "link", "add") == []
        assert runner.matching("sysctl", "-w") == []
        assert [c for c in runner.calls if "-N" in c or "-I" in c or "-D" in c] == []

    async def test_static_rules_are_flushed_then_rebuilt_and_dnat_chain_is_kept(self) -> None:
        runner = FakeCommandRunner()
        _present(runner)

        await _network(runner).init()

        flushed = [c[-1] for c in runner.calls if "-F" in c]
        assert flushed == [f"{BR}-POSTROUTING", f"{BR}-FORWARD", f"{BR}-INPUT"]
        fwd = [c for c in runner.calls if c[-1] != "-F" and f"{BR}-FORWARD" in c and "-A" in c]
        assert len(fwd) == 5

    async def test_failure_raises(self) -> None:
        runner = FakeCommandRunner()
        _present(runner)
        runner.failing.add(("ip", "link", "set", BR, "up"))

        with pytest.raises(KernelNetworkSetupFailed):
            await _network(runner).init()


class TestSetup:
    async def test_command_sequence(self) -> None:
        runner = FakeCommandRunner()
        kid = _kid()
        veth = f"bai{kid.hex[:12]}"
        ns = f"{BR}-{kid}"

        address = await _network(runner).setup(kid)

        assert address == IPv4Address("172.30.9.2")
        assert runner.calls[:8] == [
            ("ip", "netns", "add", ns),
            ("ip", "link", "add", veth, "type", "veth", "peer", "name", "eth0", "netns", ns),
            ("ip", "link", "set", veth, "master", BR),
            ("ip", "link", "set", "dev", veth, "type", "bridge_slave", "isolated", "on"),
            ("ip", "link", "set", veth, "up"),
            ("ip", "-n", ns, "addr", "add", "172.30.9.2/24", "dev", "eth0"),
            ("ip", "-n", ns, "link", "set", "eth0", "up"),
            ("ip", "-n", ns, "link", "set", "lo", "up"),
        ]
        assert runner.calls[8] == ("ip", "-n", ns, "route", "add", "default", "via", "172.30.9.1")
        assert len(veth) == 15

    async def test_one_dnat_rule_per_forward_with_the_kernel_comment(self) -> None:
        runner = FakeCommandRunner()
        kid = _kid()

        net = _network(runner)
        await net.setup(kid)
        await net.publish(kid, [PortForward(32000, 7681), PortForward(32001, 2200)])

        rules = [c for c in runner.calls if c[:5] == ("iptables", "-w", "-t", "nat", "-A")]
        head: tuple[str, ...] = ("iptables", "-w", "-t", "nat", "-A", f"{BR}-DNAT", "-p", "tcp")
        comment: tuple[str, ...] = ("-m", "comment", "--comment", f"bai-kernel={kid}")
        assert rules == [
            head
            + ("--dport", str(hp))
            + comment
            + ("-j", "DNAT", "--to-destination", f"172.30.9.2:{cp}")
            for hp, cp in ((32000, 7681), (32001, 2200))
        ]

    @pytest.mark.parametrize(
        ("bind_host", "expect_match"), [("10.0.0.5", True), ("", False), ("0.0.0.0", False)]
    )
    async def test_destination_match_only_for_a_specific_bind_host(
        self, bind_host: str, expect_match: bool
    ) -> None:
        runner = FakeCommandRunner()

        net = _network(runner, bind_host=bind_host)
        kid = _kid()
        await net.setup(kid)
        await net.publish(kid, [PortForward(32000, 7681)])

        rule = runner.matching("iptables")[0]
        assert ("-d" in rule) is expect_match
        if expect_match:
            assert rule[rule.index("-d") + 1] == "10.0.0.5/32"

    async def test_addresses_are_distinct_and_reused_after_teardown(self) -> None:
        runner = FakeCommandRunner()
        net = _network(runner)
        first, second = _kid(), _kid()

        a1 = await net.setup(first)
        a2 = await net.setup(second)
        await net.teardown(first)
        a3 = await net.setup(_kid())

        assert (a1, a2) == (IPv4Address("172.30.9.2"), IPv4Address("172.30.9.3"))
        assert a3 == a1

    async def test_exhausted_subnet(self) -> None:
        net = _network(FakeCommandRunner(), subnet=IPv4Network("172.30.9.0/30"))
        await net.setup(_kid())

        with pytest.raises(KernelAddressExhausted):
            await net.setup(_kid())

    async def test_restored_address_is_not_handed_out(self) -> None:
        net = _network(FakeCommandRunner())
        net.restore(_kid(), IPv4Address("172.30.9.2"))

        assert await net.setup(_kid()) == IPv4Address("172.30.9.3")

    def test_netns_path(self) -> None:
        kid = _kid()

        assert _network(FakeCommandRunner()).netns_path(kid) == f"/run/netns/{BR}-{kid}"

    async def test_failure_raises(self) -> None:
        runner = FakeCommandRunner()
        runner.failing.add(("ip", "netns", "add"))

        with pytest.raises(KernelNetworkSetupFailed):
            await _network(runner).setup(_kid())

    async def test_publish_without_setup_raises_a_network_error(self) -> None:
        with pytest.raises(KernelNetworkSetupFailed, match="setup did not run"):
            await _network(FakeCommandRunner()).publish(_kid(), [PortForward(32000, 22)])


def _dnat_listing(*kids: KernelId, quoted: bool = False) -> str:
    lines = [f"-N {BR}-DNAT"]
    for n, kid in enumerate(kids):
        comment = f'"bai-kernel={kid}"' if quoted else f"bai-kernel={kid}"
        lines.append(
            f"-A {BR}-DNAT -p tcp -m tcp --dport {32000 + n} -m comment --comment {comment}"
            f" -j DNAT --to-destination 172.30.9.{n + 2}:80"
        )
    return "\n".join(lines) + "\n"


class TestTeardown:
    @pytest.mark.parametrize("quoted", [False, True])
    async def test_only_this_kernels_rules_are_deleted(self, quoted: bool) -> None:
        runner = FakeCommandRunner()
        mine, other = _kid(), _kid()
        runner.script(
            ["iptables", "-w", "-t", "nat", "-S"], _dnat_listing(mine, other, quoted=quoted)
        )

        await _network(runner).teardown(mine)

        deletes = [c for c in runner.calls if "-D" in c]
        assert len(deletes) == 1
        assert deletes[0][:6] == ("iptables", "-w", "-t", "nat", "-D", f"{BR}-DNAT")
        assert f"bai-kernel={mine}" in deletes[0]
        assert "32000" in deletes[0]

    async def test_veth_and_netns_are_removed_after_the_rules(self) -> None:
        runner = FakeCommandRunner()
        kid = _kid()
        ns = f"{BR}-{kid}"
        runner.script(["iptables", "-w", "-t", "nat", "-S"], _dnat_listing(kid))
        runner.script(["ip", "netns", "list"], f"{ns} (id: 3)\nother\n")

        await _network(runner).teardown(kid)

        ops = [c for c in runner.calls if "-D" in c or "del" in c]
        assert [c[0] for c in ops] == ["iptables", "ip", "ip"]
        assert ops[1] == ("ip", "link", "del", f"bai{kid.hex[:12]}")
        assert ops[2] == ("ip", "netns", "del", ns)

    async def test_absent_pieces_are_skipped(self) -> None:
        runner = FakeCommandRunner()
        runner.script(["iptables", "-w", "-t", "nat", "-S"], returncode=1)
        runner.script(["ip", "link", "show"], returncode=1)

        await _network(runner).teardown(_kid())

        assert [c for c in runner.calls if "-D" in c or "del" in c] == []

    async def test_second_teardown_deletes_nothing(self) -> None:
        runner = FakeCommandRunner()
        kid = _kid()
        net = _network(runner)
        await net.setup(kid)
        await net.teardown(kid)
        runner.calls.clear()
        runner.script(["ip", "link", "show"], returncode=1)

        await net.teardown(kid)

        assert [c for c in runner.calls if "-D" in c or "del" in c] == []


class TestSweep:
    async def test_stale_netns_and_rules_are_removed(self) -> None:
        runner = FakeCommandRunner()
        alive, stale_ns, stale_rule = _kid(), _kid(), _kid()
        runner.script(
            ["ip", "netns", "list"],
            f"{BR}-{alive} (id: 1)\n{BR}-{stale_ns}\nother-{stale_ns}\n{BR}-notauuid\n",
        )
        runner.script(["iptables", "-w", "-t", "nat", "-S"], _dnat_listing(alive, stale_rule))

        await _network(runner).sweep([alive])

        assert [c[-1] for c in runner.matching("ip", "netns", "del")] == [f"{BR}-{stale_ns}"]
        assert {c[-1] for c in runner.matching("ip", "link", "del")} == {
            f"bai{stale_ns.hex[:12]}",
            f"bai{stale_rule.hex[:12]}",
        }
        deleted = [c for c in runner.calls if "-D" in c]
        assert len(deleted) == 1
        assert f"bai-kernel={stale_rule}" in deleted[0]

    async def test_foreign_names_are_untouched(self) -> None:
        runner = FakeCommandRunner()
        runner.script(["ip", "netns", "list"], f"cni-{_kid()}\nbai-t2-{_kid()}\n")
        runner.script(["iptables", "-w", "-t", "nat", "-S"], "-N x\n-A DOCKER -p tcp -j DNAT\n")

        await _network(runner).sweep([])

        assert [c for c in runner.calls if "-D" in c or "del" in c] == []

    async def test_a_failing_teardown_does_not_stop_the_sweep(self) -> None:
        runner = FakeCommandRunner()
        first, second = _kid(), _kid()
        runner.script(["ip", "netns", "list"], f"{BR}-{first}\n{BR}-{second}\n")
        runner.failing.add(("ip", "link", "show", "dev", f"bai{first.hex[:12]}"))
        runner.failing.add(("ip", "link", "show", "dev", f"bai{second.hex[:12]}"))

        await _network(runner).sweep([])

        assert len(runner.matching("ip", "link", "show")) == 2


class TestRunCommand:
    async def test_success(self) -> None:
        result = await run_command("echo", "hi")

        assert (result.returncode, result.stdout) == (0, "hi\n")

    async def test_non_zero_exit_raises_with_stderr(self) -> None:
        with pytest.raises(KernelNetworkSetupFailed, match="boom"):
            await run_command("sh", "-c", "echo boom >&2; exit 3")

    async def test_non_zero_exit_is_returned_without_check(self) -> None:
        assert (await run_command("sh", "-c", "exit 3", check=False)).returncode == 3

    async def test_missing_binary_raises(self) -> None:
        with pytest.raises(KernelNetworkSetupFailed, match="cannot run"):
            await run_command("bai-no-such-binary-xyz")

    async def test_timeout_raises_and_kills(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("ai.backend.agent.containerd.network._COMMAND_TIMEOUT_SEC", 0.2)

        with pytest.raises(KernelNetworkSetupFailed, match="timed out"):
            await run_command("sleep", "5")

    async def test_cancellation_kills_the_child(self) -> None:
        task = asyncio.create_task(run_command("sleep", "30"))
        procs: list[psutil.Process] = []
        for _ in range(100):
            procs = [p for p in psutil.Process().children() if p.name() == "sleep"]
            if procs:
                break
            await asyncio.sleep(0.05)
        assert len(procs) == 1

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        for _ in range(100):
            if not procs[0].is_running() or procs[0].status() == psutil.STATUS_ZOMBIE:
                break
            await asyncio.sleep(0.05)
        assert not procs[0].is_running() or procs[0].status() == psutil.STATUS_ZOMBIE
