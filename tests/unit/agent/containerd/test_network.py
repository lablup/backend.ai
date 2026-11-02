from __future__ import annotations

import asyncio
import uuid

import psutil
import pytest

from ai.backend.agent.containerd.network import KernelNetwork, run_command
from ai.backend.agent.errors.containerd import KernelNetworkSetupFailed
from ai.backend.common.types import KernelId

from .fakes import FakeCommandRunner


def _kid() -> KernelId:
    return KernelId(uuid.uuid4())


class TestSetup:
    async def test_netns_with_loopback_only(self) -> None:
        runner = FakeCommandRunner()
        kid = _kid()

        await KernelNetwork(run=runner).setup(kid)

        assert runner.calls == [
            ("ip", "netns", "add", f"bai-{kid}"),
            ("ip", "-n", f"bai-{kid}", "link", "set", "lo", "up"),
        ]

    def test_netns_path(self) -> None:
        kid = _kid()

        assert KernelNetwork().netns_path(kid) == f"/run/netns/bai-{kid}"

    async def test_failure_raises(self) -> None:
        runner = FakeCommandRunner()
        runner.failing.add(("ip", "netns", "add"))

        with pytest.raises(KernelNetworkSetupFailed):
            await KernelNetwork(run=runner).setup(_kid())


class TestTeardown:
    async def test_netns_is_removed(self) -> None:
        runner = FakeCommandRunner()
        kid = _kid()
        runner.script(["ip", "netns", "list"], f"bai-{kid} (id: 3)\nother\n")

        await KernelNetwork(run=runner).teardown(kid)

        assert runner.matching("ip", "netns", "del") == [("ip", "netns", "del", f"bai-{kid}")]

    async def test_absent_netns_is_skipped(self) -> None:
        runner = FakeCommandRunner()
        runner.script(["ip", "netns", "list"], f"bai-{_kid()}\n")

        await KernelNetwork(run=runner).teardown(_kid())

        assert runner.matching("ip", "netns", "del") == []


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
