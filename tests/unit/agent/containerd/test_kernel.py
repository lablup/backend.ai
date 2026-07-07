"""Unit tests for ContainerdKernel runner-delegating methods (runner injected via __new__)."""

import io
import json
import tarfile
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.errors.kernel import KernelRunnerNotInitializedError
from ai.backend.common.dto.agent.response import CodeCompletionResult


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def feed_and_get_status(self) -> dict[str, Any]:
        self.calls.append("status")
        return {"status": "idle"}

    async def feed_interrupt(self) -> None:
        self.calls.append("interrupt")

    async def feed_and_get_completion(self, text: str, opts: Any) -> CodeCompletionResult:
        self.calls.append("completion")
        return CodeCompletionResult.success({"suggestions": ["print"]})

    async def feed_start_service(self, body: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(f"start_service:{body['name']}")
        return {"status": "started"}

    async def feed_start_model_service(self, info: Any) -> dict[str, Any]:
        self.calls.append("model_service")
        return {"status": "started"}

    async def feed_shutdown_service(self, service: str) -> None:
        self.calls.append(f"shutdown:{service}")

    async def feed_service_apps(self) -> dict[str, Any]:
        self.calls.append("service_apps")
        return {"status": "done", "data": []}


def _kernel(
    runner: FakeRunner | None,
    *,
    service_ports: list[Any] | None = None,
    data: dict[str, Any] | None = None,
) -> ContainerdKernel:
    k = ContainerdKernel.__new__(ContainerdKernel)
    k.runner = cast(Any, runner)
    k.service_ports = service_ports or []
    k.data = data or {}
    return k


class TestRunnerDelegation:
    async def test_check_status(self) -> None:
        r = FakeRunner()
        assert await _kernel(r).check_status() == {"status": "idle"}
        assert r.calls == ["status"]

    async def test_interrupt(self) -> None:
        r = FakeRunner()
        assert await _kernel(r).interrupt_kernel() == {"status": "finished"}
        assert "interrupt" in r.calls

    async def test_get_completions_wraps_result(self) -> None:
        resp = await _kernel(FakeRunner()).get_completions("pri", {})
        assert resp.result.status == "finished"  # CodeCompletionResult.success

    async def test_shutdown_and_service_apps(self) -> None:
        r = FakeRunner()
        k = _kernel(r)
        await k.shutdown_service("jupyter")
        await k.get_service_apps()
        assert r.calls == ["shutdown:jupyter", "service_apps"]


class TestStartService:
    async def test_invalid_service_name(self) -> None:
        k = _kernel(
            FakeRunner(),
            service_ports=[{"name": "jupyter", "container_ports": [8080], "protocol": "http"}],
        )
        result = await k.start_service("nope", {})
        assert result == {"status": "failed", "error": "invalid service name"}

    async def test_valid_service_feeds_runner(self) -> None:
        r = FakeRunner()
        k = _kernel(
            r, service_ports=[{"name": "jupyter", "container_ports": [8080], "protocol": "http"}]
        )
        result = await k.start_service("jupyter", {})
        assert result == {"status": "started"}
        assert "start_service:jupyter" in r.calls

    async def test_blocked_service_ports(self) -> None:
        k = _kernel(FakeRunner(), data={"block_service_ports": True})
        result = await k.start_service("jupyter", {})
        assert result == {"status": "failed", "error": "operation blocked"}


class TestRunnerNotInitialized:
    async def test_check_status_without_runner_raises(self) -> None:
        with pytest.raises(KernelRunnerNotInitializedError):
            await _kernel(None).check_status()


def _fs_kernel(scratch_root: Any, kernel_id: str = "kern-1") -> ContainerdKernel:
    k = ContainerdKernel.__new__(ContainerdKernel)
    k.data = {"container_id": kernel_id}
    k.kernel_id = cast(Any, kernel_id)
    k.agent_config = cast(Any, {"container": {"scratch-root": scratch_root}})
    (scratch_root / kernel_id / "work").mkdir(parents=True, exist_ok=True)
    return k


class TestFileOps:
    async def test_accept_then_download_single_roundtrips(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        await k.accept_file("hello.txt", b"hi there")
        assert (tmp_path / "kern-1" / "work" / "hello.txt").read_bytes() == b"hi there"
        assert await k.download_single("hello.txt") == b"hi there"

    async def test_accept_creates_parent_dirs(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        await k.accept_file("sub/dir/f.bin", b"x")
        assert (tmp_path / "kern-1" / "work" / "sub" / "dir" / "f.bin").read_bytes() == b"x"

    async def test_download_file_returns_tar(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        await k.accept_file("a.txt", b"data")
        tar_bytes = await k.download_file("a.txt")
        with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
            assert tar.getnames() == ["a.txt"]

    async def test_list_files_reports_entries(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        await k.accept_file("one.txt", b"1")
        await k.accept_file("two.txt", b"22")
        result = await k.list_files(".")
        names = {e["filename"] for e in json.loads(result["files"])}
        assert names == {"one.txt", "two.txt"}
        assert result["errors"] == ""

    async def test_escape_outside_home_is_rejected(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        with pytest.raises(PermissionError):
            await k.accept_file("../../etc/passwd", b"x")
