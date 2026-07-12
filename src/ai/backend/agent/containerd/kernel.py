"""Containerd kernel + code runner (BEP-1062 / containerd agent backend).

Mirrors the Docker kernel contract on containerd's native task model. REPL/service ops go
through the code runner (network-based); file transfer and logs work off the host scratch
mount + captured task stdout; session-to-image commit builds the image over the containerd
Diff/Content/Images services.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import textwrap
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any, override

from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime, container_log_path
from ai.backend.agent.containerd.runtime.interface import ExecResult
from ai.backend.agent.errors.kernel import KernelRunnerNotInitializedError
from ai.backend.agent.kernel import (
    AbstractCodeRunner,
    AbstractKernel,
)
from ai.backend.agent.types import AgentEventData, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.lock import FileLock
from ai.backend.common.types import CommitStatus, KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_MAX_DOWNLOAD_SIZE = 1048576  # 1 MiB, matching the Docker backend
_CONTAINER_HOME = PurePosixPath("/home/work")
_EXEC_TIMEOUT = 30.0
# The kernel-runner's own interpreter, bind-mounted into every kernel: the only one guaranteed to
# exist regardless of what the image ships (the Docker backend's list_files relies on it too).
_KRUNNER_PYTHON = "/opt/backend.ai/bin/python"

# Scandir the target and print one JSON record per entry — byte-for-byte the same shape the Docker
# backend produces, since the manager parses it.
_SCANDIR_CODE = textwrap.dedent("""
    import json, os, stat, sys
    files = []
    for f in os.scandir(sys.argv[1]):
        fstat = f.stat(follow_symlinks=False)
        files.append({
            'mode': stat.filemode(fstat.st_mode),
            'size': fstat.st_size,
            'ctime': fstat.st_ctime,
            'mtime': fstat.st_mtime,
            'atime': fstat.st_atime,
            'filename': f.name,
        })
    print(json.dumps(files))
""")

# Tar the target to stdout, aborting once the archive exceeds the cap so a huge directory cannot
# be streamed through the agent's memory.
_TAR_TO_STDOUT_CODE = textwrap.dedent("""
    import io, os, sys, tarfile
    path, limit = sys.argv[1], int(sys.argv[2])
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as tar:
        tar.add(path, arcname=os.path.basename(path))
        if buf.tell() > limit:
            sys.exit('Too large archive file exceeding 1 MiB')
    data = buf.getvalue()
    if len(data) > limit:
        sys.exit('Too large archive file exceeding 1 MiB')
    sys.stdout.buffer.write(data)
""")

_READ_SINGLE_CODE = textwrap.dedent("""
    import os, sys
    path, limit = sys.argv[1], int(sys.argv[2])
    if not os.path.isfile(path):
        sys.exit('Expected a single file at %s' % path)
    if os.path.getsize(path) > limit:
        sys.exit('Too large file exceeding 1 MiB')
    with open(path, 'rb') as f:
        sys.stdout.buffer.write(f.read())
""")


class ContainerdKernel(AbstractKernel):
    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        network_id: str,
        image: ImageRef,
        version: int,
        *,
        agent_config: Mapping[str, Any],
        resource_spec: Any,
        service_ports: Any,
        environ: Mapping[str, Any],
        data: dict[str, Any],
    ) -> None:
        super().__init__(
            ownership_data,
            network_id,
            image,
            version,
            agent_config=agent_config,
            resource_spec=resource_spec,
            service_ports=service_ports,
            data=data,
            environ=environ,
        )

    @override
    async def close(self) -> None:
        pass

    @override
    async def create_code_runner(
        self,
        event_producer: EventProducer,
        *,
        client_features: frozenset[str],
        api_version: int,
    ) -> AbstractCodeRunner:
        return await ContainerdCodeRunner.new(
            self.kernel_id,
            self.session_id,
            event_producer,
            # the container's own LOCAL address: the agent is on this node and the host is that
            # bridge's gateway, so the REPL needs no published port. kernel_host is the agent's
            # advertised address, for consumers that are not on this node.
            kernel_host=self.data.get("repl_host") or self.data["kernel_host"],
            repl_in_port=self.data["repl_in_port"],
            repl_out_port=self.data["repl_out_port"],
            exec_timeout=0,
            client_features=client_features,
        )

    def _require_runner(self) -> AbstractCodeRunner:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        return self.runner

    @override
    async def check_status(self) -> dict[str, Any] | None:
        return await self._require_runner().feed_and_get_status()

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]) -> CodeCompletionResp:
        result = await self._require_runner().feed_and_get_completion(text, opts)
        return CodeCompletionResp(result=result)

    @override
    async def get_logs(self) -> dict[str, Any]:
        # The runtime captures the task's stdout+stderr to a host log file (keyed by the
        # container id, which is the kernel id here); read it back.
        #
        # Serve at most `container_logs.max_length` — the bound the Docker backend gets from its
        # log driver (max-size x max-file). Without it a chatty kernel's entire log is read into
        # memory and shipped to the manager. We keep the TAIL, which is what a log query wants.
        #
        # This bounds what is SERVED, not what is on disk: the containerd shim owns the write end
        # of this file and offers no rotation, so it grows until remove_container unlinks it.
        # Bounding the disk side means rotating behind the shim's open fd; not attempted here.
        log_path = container_log_path(self.data["container_id"])
        max_length = int(self.agent_config["container-logs"]["max-length"])

        def _read() -> str:
            try:
                with log_path.open("rb") as f:
                    size = f.seek(0, io.SEEK_END)
                    f.seek(max(0, size - max_length), io.SEEK_SET)
                    return f.read().decode("utf-8", errors="replace")
            except FileNotFoundError:
                return ""

        return {"logs": await asyncio.to_thread(_read)}

    @override
    async def interrupt_kernel(self) -> dict[str, Any]:
        await self._require_runner().feed_interrupt()
        return {"status": "finished"}

    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> dict[str, Any]:
        runner = self._require_runner()
        if self.data.get("block_service_ports", False):
            return {"status": "failed", "error": "operation blocked"}
        for sport in self.service_ports:
            if sport["name"] == service:
                break
        else:
            return {"status": "failed", "error": "invalid service name"}
        return await runner.feed_start_service({
            "name": service,
            "port": sport["container_ports"][0],
            "ports": sport["container_ports"],
            "protocol": sport["protocol"],
            "options": opts,
        })

    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> dict[str, Any]:
        return await self._require_runner().feed_start_model_service(model_service)

    @override
    async def shutdown_service(self, service: str) -> None:
        await self._require_runner().feed_shutdown_service(service)

    def _commit_lock_path(self, kernel_id: KernelId, subdir: str) -> Path:
        base = Path(self.agent_config["agent"]["image-commit-path"])
        return base / subdir / "lock" / str(kernel_id)

    @override
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        if self._commit_lock_path(kernel_id, subdir).exists():
            return CommitStatus.ONGOING
        return CommitStatus.READY

    @override
    async def commit(
        self,
        kernel_id: KernelId,
        subdir: str,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] | None = None,
    ) -> None:
        # Commit the container's rootfs into a new local image via the containerd Diff +
        # Content + Images services (a short-lived runtime client to the local socket).
        lock_path = self._commit_lock_path(kernel_id, subdir)
        target_ref = canonical or f"localhost/committed-{kernel_id}:latest"
        await asyncio.to_thread(lock_path.parent.mkdir, parents=True, exist_ok=True)
        commit_timeout = float(self.agent_config["api"]["commit-timeout"])
        try:
            async with FileLock(path=lock_path, timeout=0.1, remove_when_unlock=True):
                runtime = ContainerdGrpcRuntime(namespace="backend-ai")
                await runtime.open()
                try:
                    async with asyncio.timeout(commit_timeout):
                        await runtime.commit_container(
                            str(self.data["container_id"]),
                            base_image_ref=self.image.canonical,
                            target_ref=target_ref,
                            labels=extra_labels or {},
                        )
                        if filename:
                            # Export the freshly committed image as the downloadable artifact,
                            # then drop it: it only existed to be exported (the Docker backend
                            # deletes its intermediate image the same way). Skipping this used to
                            # leave the caller with a successful commit and no file at all.
                            dest = (
                                Path(self.agent_config["agent"]["image-commit-path"])
                                / subdir
                                / filename
                            )
                            try:
                                await runtime.export_image(target_ref, dest)
                            finally:
                                if canonical is None:
                                    await runtime.remove_image(target_ref)
                finally:
                    await runtime.close()
        except TimeoutError:
            log.warning("commit(k:{}): already being committed", kernel_id)

    @override
    async def get_service_apps(self) -> dict[str, Any]:
        return await self._require_runner().feed_service_apps()

    def _host_work_dir(self) -> Path:
        return Path(self.agent_config["container"]["scratch-root"]) / str(self.kernel_id) / "work"

    def _to_host_path(self, container_path: os.PathLike[str] | str) -> Path:
        """Map a container path under /home/work to its host scratch path, rejecting any
        path that escapes /home/work (that dir IS a host bind mount, so no container access
        is needed for file I/O)."""
        abspath = PurePosixPath(os.path.normpath(_CONTAINER_HOME / os.fspath(container_path)))
        if not abspath.is_relative_to(_CONTAINER_HOME):
            raise PermissionError("Not allowed to access files outside /home/work")
        work = self._host_work_dir().resolve()
        host = (work / abspath.relative_to(_CONTAINER_HOME)).resolve(strict=False)
        if host != work and not host.is_relative_to(work):
            raise PermissionError("Not allowed to access files outside /home/work")
        return host

    @override
    async def accept_file(self, container_path: os.PathLike[str] | str, filedata: bytes) -> None:
        host = self._to_host_path(container_path)

        def _write() -> None:
            host.parent.mkdir(parents=True, exist_ok=True)
            host.write_bytes(filedata)

        await asyncio.to_thread(_write)

    def _to_container_path(self, container_path: os.PathLike[str] | str) -> PurePosixPath:
        """Normalize a user-supplied path and confine it to /home/work."""
        abspath = PurePosixPath(os.path.normpath(_CONTAINER_HOME / os.fspath(container_path)))
        if not abspath.is_relative_to(_CONTAINER_HOME):
            raise PermissionError("Not allowed to access files outside /home/work")
        return abspath

    async def _exec(self, args: list[str], *, timeout_sec: float = _EXEC_TIMEOUT) -> ExecResult:
        """Run a command in this kernel's container.

        The file APIs must look at the container's own mount namespace, not the host scratch: a
        vfolder is bind-mounted into the container at /home/work/<name> and does not exist under
        the host's scratch work dir at all, so reading the host would report an empty directory
        for every vfolder.
        """
        runtime = ContainerdGrpcRuntime(namespace="backend-ai")
        await runtime.open()
        try:
            return await runtime.exec_in_container(
                str(self.data["container_id"]), args, timeout_sec=timeout_sec
            )
        finally:
            await runtime.close()

    @override
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        abspath = self._to_container_path(container_path)
        # Tar the target inside the container and stream it out through stdout, the same archive
        # shape the Docker backend gets from container.get_archive().
        result = await self._exec([
            _KRUNNER_PYTHON,
            "-c",
            _TAR_TO_STDOUT_CODE,
            str(abspath),
            str(_MAX_DOWNLOAD_SIZE),
        ])
        if result.exit_code != 0:
            raise RuntimeError(
                f"Could not download the archive at {abspath}: "
                f"{result.stderr.decode('utf-8', errors='replace').strip()}"
            )
        if len(result.stdout) > _MAX_DOWNLOAD_SIZE:
            raise ValueError("Too large archive file exceeding 1 MiB")
        return result.stdout

    @override
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        abspath = self._to_container_path(container_path)
        result = await self._exec([
            _KRUNNER_PYTHON,
            "-c",
            _READ_SINGLE_CODE,
            str(abspath),
            str(_MAX_DOWNLOAD_SIZE),
        ])
        if result.exit_code != 0:
            raise ValueError(
                f"Could not read {abspath}: "
                f"{result.stderr.decode('utf-8', errors='replace').strip()}"
            )
        return result.stdout

    @override
    async def list_files(self, container_path: os.PathLike[str] | str) -> dict[str, Any]:
        abspath = self._to_container_path(container_path)
        result = await self._exec([_KRUNNER_PYTHON, "-c", _SCANDIR_CODE, str(abspath)])
        return {
            "files": result.stdout.decode("utf-8", errors="replace"),
            "errors": result.stderr.decode("utf-8", errors="replace"),
            "abspath": str(container_path),
        }

    @override
    async def notify_event(self, evdata: AgentEventData) -> None:
        await self._require_runner().feed_event(evdata)


class ContainerdCodeRunner(AbstractCodeRunner):
    kernel_host: str
    repl_in_port: int
    repl_out_port: int

    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event_producer: EventProducer,
        *,
        kernel_host: str,
        repl_in_port: int,
        repl_out_port: int,
        exec_timeout: float = 0,
        client_features: frozenset[str] | None = None,
    ) -> None:
        super().__init__(
            kernel_id,
            session_id,
            event_producer,
            exec_timeout=exec_timeout,
            client_features=client_features,
        )
        self.kernel_host = kernel_host
        self.repl_in_port = repl_in_port
        self.repl_out_port = repl_out_port

    @override
    async def get_repl_in_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_in_port}"

    @override
    async def get_repl_out_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_out_port}"
