"""Containerd kernel + code runner (BEP-1062 / containerd agent backend).

Mirrors the Docker kernel contract on containerd's native task model. REPL/service ops go
through the code runner (network-based); session-to-image commit builds the image over the
containerd Diff/Content/Images services.

The file APIs read the host, not the container. Everything under /home/work is a host bind mount --
the scratch work dir, with each vfolder mounted over a subdirectory of it -- so a container path
resolves to a host path through the kernel's own mount table. That is what dockerd does for
`docker cp` (container.ResolvePath), and it is why that works on a container that is not running.
Going through the container instead (which is what this used to do, via exec) means no files can be
fetched from a kernel that has exited -- the one moment a user most wants them.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import stat
import tarfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any, override

from ai.backend.agent.containerd.logs import read_log_tail
from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime, container_log_path
from ai.backend.agent.errors.kernel import KernelRunnerNotInitializedError
from ai.backend.agent.kernel import (
    AbstractCodeRunner,
    AbstractKernel,
)
from ai.backend.agent.types import AgentEventData, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.json import dump_json_str
from ai.backend.common.lock import FileLock
from ai.backend.common.types import CommitStatus, KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_MAX_DOWNLOAD_SIZE = 1048576  # 1 MiB, matching the Docker backend
_CONTAINER_HOME = PurePosixPath("/home/work")


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
        # The log is a set of files, not one: the active one the shim appends to plus the rotated
        # ones, exactly as Docker's log driver keeps them. Read across them (oldest first) and serve
        # at most `container_logs.max_length` — the same window `docker logs` returns for these
        # kernels. Reading only the active file would return almost nothing right after a rotation.
        active = container_log_path(self.data["container_id"])
        max_length = int(self.agent_config["container-logs"]["max-length"])
        raw = await asyncio.to_thread(read_log_tail, active, max_length)
        return {"logs": raw.decode("utf-8", errors="replace")}

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
        """Map a path under /home/work to the host path that actually backs it.

        Everything under /home/work is a host bind mount — the scratch work dir, with each vfolder
        mounted over a subdirectory of it — so a container path resolves to a host path by matching
        it against the kernel's own mount table, longest target first. This is what dockerd does for
        `docker cp` (container.ResolvePath), and it is why that works on a container that is not
        running: no process, no namespace, and no runtime are involved.

        The mount table comes from the resource spec, which is written to (and read back from)
        resource.txt, so it survives an agent restart with the kernel.
        """
        abspath = self._to_container_path(container_path)
        base_target = _CONTAINER_HOME
        base_source = self._host_work_dir()
        for mount in self.resource_spec.mounts:
            if mount.source is None:
                continue
            target = PurePosixPath(str(mount.target))
            if abspath != target and not abspath.is_relative_to(target):
                continue
            if len(target.parts) >= len(base_target.parts):
                base_target, base_source = target, Path(str(mount.source))
        root = base_source.resolve()
        host = (root / abspath.relative_to(base_target)).resolve(strict=False)
        # A symlink in the scratch may point anywhere on the host; following it would hand the user
        # a file the container itself could never open.
        if host != root and not host.is_relative_to(root):
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

    @override
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        """A tar of the target, the same archive shape the Docker backend gets from
        container.get_archive() (one member, named after the target)."""
        host = self._to_host_path(container_path)

        def _tar() -> bytes:
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w") as tar:
                tar.add(host, arcname=host.name)
                if buf.tell() > _MAX_DOWNLOAD_SIZE:
                    raise ValueError("Too large archive file exceeding 1 MiB")
            data = buf.getvalue()
            if len(data) > _MAX_DOWNLOAD_SIZE:
                raise ValueError("Too large archive file exceeding 1 MiB")
            return data

        try:
            return await asyncio.to_thread(_tar)
        except FileNotFoundError as e:
            raise RuntimeError(f"Could not download the archive at {container_path}") from e

    @override
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        host = self._to_host_path(container_path)

        def _read() -> bytes:
            if not host.is_file():
                raise ValueError(f"Expected a single file at {container_path}")
            if host.stat().st_size > _MAX_DOWNLOAD_SIZE:
                raise ValueError("Too large file exceeding 1 MiB")
            return host.read_bytes()

        return await asyncio.to_thread(_read)

    @override
    async def list_files(self, container_path: os.PathLike[str] | str) -> dict[str, Any]:
        host = self._to_host_path(container_path)

        def _scandir() -> tuple[str, str]:
            files = []
            try:
                for entry in os.scandir(host):
                    fstat = entry.stat(follow_symlinks=False)
                    files.append({
                        "mode": stat.filemode(fstat.st_mode),
                        "size": fstat.st_size,
                        "ctime": fstat.st_ctime,
                        "mtime": fstat.st_mtime,
                        "atime": fstat.st_atime,
                        "filename": entry.name,
                    })
            except OSError as e:
                return "", str(e)
            return dump_json_str(files), ""

        # The manager parses `files` as the JSON list the Docker backend produces, so the shape of
        # each record is a contract, not a detail.
        files_json, errors = await asyncio.to_thread(_scandir)
        return {
            "files": files_json,
            "errors": errors,
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
