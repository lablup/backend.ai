from __future__ import annotations

import asyncio
import uuid
from ipaddress import IPv4Address, IPv4Network

import pytest

from ai.backend.agent.containerd.network import KernelNetwork, run_command
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

        assert runner.calls == [
            ("ip", "-d", "link", "show", "dev", "bai0"),
            ("ip", "link", "add", "bai0", "type", "bridge"),
            ("ip", "addr", "replace", "172.30.0.1/24", "dev", "bai0"),
            ("ip", "link", "set", "bai0", "up"),
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
        network = KernelNetwork("bai0", IPv4Network("172.30.0.0/30"), run=runner)
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
