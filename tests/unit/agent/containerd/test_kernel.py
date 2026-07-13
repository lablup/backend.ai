"""Unit tests for ContainerdKernel runner-delegating methods (runner injected via __new__)."""

import io
import json
import tarfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.kernel import ContainerdKernel
from ai.backend.agent.errors.kernel import KernelRunnerNotInitializedError
from ai.backend.agent.resources import Mount
from ai.backend.common.dto.agent.response import CodeCompletionResult
from ai.backend.common.types import MountPermission, MountTypes


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


def _fs_kernel(
    scratch_root: Any,
    kernel_id: str = "kern-1",
    *,
    mounts: list[Mount] | None = None,
) -> ContainerdKernel:
    k = ContainerdKernel.__new__(ContainerdKernel)
    k.data = {"container_id": kernel_id}
    k.kernel_id = cast(Any, kernel_id)
    k.agent_config = cast(Any, {"container": {"scratch-root": scratch_root}})
    work = scratch_root / kernel_id / "work"
    work.mkdir(parents=True, exist_ok=True)
    # The mount table the real kernel carries: the scratch work dir at /home/work, plus whatever
    # vfolders were mounted over it. It is serialized into resource.txt, so it survives a restart.
    k.resource_spec = cast(
        Any,
        SimpleNamespace(
            mounts=[
                Mount(
                    MountTypes.BIND, work, Path("/home/work"), MountPermission.READ_WRITE
                ),
                *(mounts or []),
            ]
        ),
    )
    return k


class TestFileOps:
    async def test_accept_file_writes_the_host_scratch(self, tmp_path: Any) -> None:
        # accept_file stays host-side: /home/work IS the scratch bind mount, so the container sees
        # the write immediately. Docker does the same.
        k = _fs_kernel(tmp_path)
        await k.accept_file("hello.txt", b"hi there")
        assert (tmp_path / "kern-1" / "work" / "hello.txt").read_bytes() == b"hi there"

    async def test_accept_creates_parent_dirs(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        await k.accept_file("sub/dir/f.bin", b"x")
        assert (tmp_path / "kern-1" / "work" / "sub" / "dir" / "f.bin").read_bytes() == b"x"

    async def test_escape_outside_home_is_rejected(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        with pytest.raises(PermissionError):
            await k.accept_file("../../etc/passwd", b"x")

    async def test_read_paths_reject_escapes(self, tmp_path: Any) -> None:
        # Confinement must hold on every read path, not just the write one.
        k = _fs_kernel(tmp_path)
        for op in (k.list_files, k.download_file, k.download_single):
            with pytest.raises(PermissionError):
                await op("../../etc/passwd")


class TestFileOpsResolveTheHostPath:
    """The file APIs read the host, through the kernel's own mount table.

    Everything under /home/work is a host bind mount — the scratch work dir, with each vfolder
    mounted over a subdirectory of it — so a container path has a host path, and no container is
    needed to read it. This is what dockerd does for `docker cp` (container.ResolvePath), and it is
    why that works on a container that is not running. Going through the container instead (which is
    what this used to do, via exec) means no files can be fetched from a kernel that has exited —
    the one moment a user most wants them.
    """

    def _kernel_with_vfolder(self, tmp_path: Any) -> tuple[Any, Any]:
        vfolder = tmp_path / "storage" / "my-vfolder"
        vfolder.mkdir(parents=True)
        k = _fs_kernel(
            tmp_path,
            mounts=[
                Mount(
                    MountTypes.BIND,
                    vfolder,
                    Path("/home/work/my-vfolder"),
                    MountPermission.READ_WRITE,
                )
            ],
        )
        return k, vfolder

    async def test_a_vfolder_resolves_to_its_own_storage_path(self, tmp_path: Any) -> None:
        # The vfolder is NOT under the scratch work dir — it is mounted over a subdirectory of it.
        # Reading the scratch would report an empty directory and the files would be invisible.
        k, vfolder = self._kernel_with_vfolder(tmp_path)
        (vfolder / "in-vfolder.txt").write_bytes(b"abc")

        listing = json.loads((await k.list_files("my-vfolder"))["files"])

        assert [e["filename"] for e in listing] == ["in-vfolder.txt"]
        assert await k.download_single("my-vfolder/in-vfolder.txt") == b"abc"

    async def test_the_longest_mount_wins(self, tmp_path: Any) -> None:
        # /home/work/my-vfolder/x must come from the vfolder, not from the scratch that /home/work
        # itself is mounted from — both mounts match the path.
        k, vfolder = self._kernel_with_vfolder(tmp_path)
        (vfolder / "x").write_bytes(b"from the vfolder")
        decoy = tmp_path / "kern-1" / "work" / "my-vfolder"
        decoy.mkdir(parents=True)
        (decoy / "x").write_bytes(b"from the scratch, shadowed by the mount")

        assert await k.download_single("my-vfolder/x") == b"from the vfolder"

    async def test_a_scratch_file_is_read_from_the_scratch(self, tmp_path: Any) -> None:
        k, _vfolder = self._kernel_with_vfolder(tmp_path)
        (tmp_path / "kern-1" / "work" / "a.txt").write_bytes(b"hello")

        assert await k.download_single("a.txt") == b"hello"

    async def test_an_exited_kernel_can_still_be_read(self, tmp_path: Any) -> None:
        # The whole point. There is no container_id, no task, and no runtime here — and it still
        # works, because none of them were ever needed.
        k, vfolder = self._kernel_with_vfolder(tmp_path)
        (vfolder / "results.csv").write_bytes(b"1,2,3")
        k.data = {}  # the container is gone

        assert await k.download_single("my-vfolder/results.csv") == b"1,2,3"

    async def test_download_file_tars_the_target(self, tmp_path: Any) -> None:
        # Same archive shape the Docker backend returns from container.get_archive(): one member,
        # named after the target.
        k = _fs_kernel(tmp_path)
        (tmp_path / "kern-1" / "work" / "a.txt").write_bytes(b"data")

        with tarfile.open(fileobj=io.BytesIO(await k.download_file("a.txt"))) as tar:
            assert tar.getnames() == ["a.txt"]
            member = tar.extractfile("a.txt")
            assert member is not None and member.read() == b"data"

    async def test_a_directory_is_tarred_whole(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        d = tmp_path / "kern-1" / "work" / "sub"
        d.mkdir()
        (d / "f.txt").write_bytes(b"x")

        with tarfile.open(fileobj=io.BytesIO(await k.download_file("sub"))) as tar:
            assert sorted(tar.getnames()) == ["sub", "sub/f.txt"]

    async def test_download_single_refuses_a_directory(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        (tmp_path / "kern-1" / "work" / "sub").mkdir()
        with pytest.raises(ValueError, match="single file"):
            await k.download_single("sub")

    async def test_an_oversized_file_is_refused(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        (tmp_path / "kern-1" / "work" / "big.bin").write_bytes(b"x" * (1048576 + 1))
        with pytest.raises(ValueError, match="Too large"):
            await k.download_single("big.bin")

    async def test_a_symlink_out_of_the_mount_is_refused(self, tmp_path: Any) -> None:
        # On the host a symlink can point anywhere; following it would hand the user a file the
        # container itself could never open.
        k = _fs_kernel(tmp_path)
        secret = tmp_path / "secret.txt"
        secret.write_bytes(b"host secret")
        (tmp_path / "kern-1" / "work" / "escape").symlink_to(secret)

        with pytest.raises(PermissionError):
            await k.download_single("escape")

    async def test_listing_a_missing_directory_reports_the_error(self, tmp_path: Any) -> None:
        k = _fs_kernel(tmp_path)
        result = await k.list_files("nope")
        assert result["files"] == ""
        assert result["errors"]
