from collections.abc import Sequence
from typing import Any

import pytest

from ai.backend.agent.containerd.nerdctl_runtime import NerdctlError, NerdctlRuntimeClient


class FakeRunner:
    """Records argv and returns scripted (rc, stdout, stderr) per invocation."""

    def __init__(self, responses: list[tuple[int, str, str]]) -> None:
        self.responses = responses
        self.calls: list[list[str]] = []

    async def __call__(self, argv: Sequence[str]) -> tuple[int, str, str]:
        self.calls.append(list(argv))
        return self.responses.pop(0) if self.responses else (0, "", "")


def _client(runner: FakeRunner) -> NerdctlRuntimeClient:
    return NerdctlRuntimeClient(runner, nerdctl_path="nerdctl", namespace="backend-ai")


class TestArgvConstruction:
    async def test_create_uses_network_none(self) -> None:
        runner = FakeRunner([(0, "", "")])
        await _client(runner).create_container(
            "c1", image_ref="alpine:3.20", command=["sleep", "600"], oci_spec={}
        )
        argv = runner.calls[0]
        assert argv[:3] == ["nerdctl", "--namespace", "backend-ai"]
        assert "--network" in argv and argv[argv.index("--network") + 1] == "none"
        assert argv[-2:] == ["sleep", "600"]

    async def test_image_exists_maps_returncode(self) -> None:
        assert await _client(FakeRunner([(0, "", "")])).image_exists("x") is True
        assert await _client(FakeRunner([(1, "", "not found")])).image_exists("x") is False

    async def test_pull_with_creds(self) -> None:
        runner = FakeRunner([(0, "", "")])
        await _client(runner).pull_image("img", auth={"username": "u", "password": "p"})
        argv = runner.calls[0]
        assert "--creds" in argv and argv[argv.index("--creds") + 1] == "u:p"


class TestStartContainer:
    async def test_start_then_reads_pid(self) -> None:
        # 1st call: start (ok); 2nd call: inspect pid
        runner = FakeRunner([(0, "", ""), (0, "24963\n", "")])
        handle = await _client(runner).start_container("c1")
        assert handle.pid == 24963
        assert handle.container_id == "c1"
        assert runner.calls[0][3] == "start"
        assert "{{.State.Pid}}" in runner.calls[1]

    async def test_start_without_pid_raises(self) -> None:
        runner = FakeRunner([(0, "", ""), (0, "0\n", "")])  # pid 0 => no task
        with pytest.raises(NerdctlError):
            await _client(runner).start_container("c1")


class TestContainerPid:
    async def test_missing_container_returns_none(self) -> None:
        runner = FakeRunner([(1, "", "no such container")])
        assert await _client(runner).container_pid("nope") is None

    async def test_zero_pid_returns_none(self) -> None:
        runner = FakeRunner([(0, "0", "")])
        assert await _client(runner).container_pid("c1") is None


class TestFailurePropagation:
    async def test_nonzero_rc_raises(self) -> None:
        runner = FakeRunner([(125, "", "boom")])
        with pytest.raises(NerdctlError):
            await _client(runner).pull_image("img")

    async def test_kill_and_remove_tolerate_rc1(self) -> None:
        # already-dead / already-gone are non-fatal
        await _client(FakeRunner([(1, "", "not running")])).kill_container("c1", signal=9)
        await _client(FakeRunner([(1, "", "no such container")])).remove_container("c1")


def _noop_spec() -> dict[str, Any]:
    return {}
