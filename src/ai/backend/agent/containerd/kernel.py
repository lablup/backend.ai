"""Containerd-backed kernel and code runner.

``ContainerdKernel`` mirrors ``DockerKernel``: most operations delegate
to the ``ContainerdCodeRunner`` (which speaks the same ZMQ REPL protocol
the in-container krunner exposes). The container's ``/home/work`` is
bind-mounted from the host's per-kernel scratch dir, so file operations
(``accept_file``, ``download_file``, ``download_single``, ``list_files``)
read and write the host path directly — no in-container exec is needed
to inspect or transfer files there. Likewise the task's stdout/stderr
are wired to ``{scratch_dir}/container.log`` at task-create time, so
``get_logs`` is a plain host-side tail. The remaining hold-out is image
commit, which needs ``Snapshots.Commit`` + ``Images.Create`` plumbing
and is still deferred.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import stat
import tarfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any, override

from ai.backend.agent.errors import KernelRunnerNotInitializedError
from ai.backend.agent.kernel import AbstractCodeRunner, AbstractKernel
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import AgentEventData, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import CommitStatus, KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerdKernel(AbstractKernel):
    """Backend.AI kernel running as a containerd task in a custom namespace.

    Most operations are runtime-agnostic and delegate to
    ``ContainerdCodeRunner`` over the in-container ZMQ REPL. A few are
    stubbed pending follow-up wiring (see module docstring).
    """

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        network_id: str,
        image: ImageRef,
        version: int,
        *,
        agent_config: Mapping[str, Any],
        resource_spec: KernelResourceSpec,
        service_ports: Any,  # TODO: type-annotation
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
        # The kernel's REPL is reached directly at the netns-assigned IP;
        # see ContainerdKernelCreationContext.start_container which records
        # kernel_host / repl_in_port / repl_out_port into ``self.data``.
        return await ContainerdCodeRunner.new(
            self.kernel_id,
            self.session_id,
            event_producer,
            kernel_host=self.data["kernel_host"],
            repl_in_port=self.data["repl_in_port"],
            repl_out_port=self.data["repl_out_port"],
            exec_timeout=0,
            client_features=client_features,
        )

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]) -> CodeCompletionResp:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        result = await self.runner.feed_and_get_completion(text, opts)
        return CodeCompletionResp(result=result)

    @override
    async def check_status(self) -> dict[str, Any] | None:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        return await self.runner.feed_and_get_status()

    @override
    async def get_logs(self) -> dict[str, Any]:
        # The task's stdout/stderr are wired to a host file at
        # task-create time (see ContainerdKernelCreationContext
        # .start_container's stdout/stderr URIs), so log retrieval is a
        # plain host-side read. Cap the returned slice at 1 MiB — the
        # docker backend imposes a similar cap via its log driver's
        # max-size — and read the tail so the most recent output wins
        # if the file has grown beyond that.
        log_path: Path = (
            self.agent_config["container"]["scratch-root"] / str(self.kernel_id) / "container.log"
        )
        max_bytes = 1 * 1024 * 1024

        def _read_tail() -> str:
            if not log_path.is_file():
                return ""
            size = log_path.stat().st_size
            with log_path.open("rb") as fp:
                if size > max_bytes:
                    fp.seek(size - max_bytes)
                return fp.read().decode("utf-8", "replace")

        return {"logs": await asyncio.to_thread(_read_tail)}

    @override
    async def interrupt_kernel(self) -> dict[str, Any]:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        await self.runner.feed_interrupt()
        return {"status": "finished"}

    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> dict[str, Any]:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        if self.data.get("block_service_ports", False):
            return {
                "status": "failed",
                "error": "operation blocked",
            }
        for sport in self.service_ports:
            if sport["name"] == service:
                break
        else:
            return {"status": "failed", "error": "invalid service name"}
        return await self.runner.feed_start_service({
            "name": service,
            "port": sport["container_ports"][0],  # primary port
            "ports": sport["container_ports"],
            "protocol": sport["protocol"],
            "options": opts,
        })

    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> dict[str, Any]:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        return await self.runner.feed_start_model_service(model_service)

    @override
    async def shutdown_service(self, service: str) -> None:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        await self.runner.feed_shutdown_service(service)

    @override
    async def get_service_apps(self) -> dict[str, Any]:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        return await self.runner.feed_service_apps()

    def _get_commit_path(self, kernel_id: KernelId, subdir: str) -> tuple[Path, Path]:
        base_commit_path: Path = self.agent_config["agent"]["image-commit-path"]
        commit_path = base_commit_path / subdir
        lock_path = commit_path / "lock" / str(kernel_id)
        return commit_path, lock_path

    @override
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        _, lock_path = self._get_commit_path(kernel_id, subdir)
        if lock_path.exists():
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
        # Committing a running containerd task into a new image involves
        # Snapshots.Commit + Images.Create + content-store layer writes;
        # that machinery is deferred. The agent already creates the lock
        # path via check_duplicate_commit so the manager request flow
        # surfaces a clean NotImplementedError instead of a partial state.
        del kernel_id, subdir, canonical, filename, extra_labels
        raise NotImplementedError("containerd kernel commit is not implemented yet")

    @override
    async def accept_file(self, container_path: os.PathLike[str] | str, filedata: bytes) -> None:
        # The kernel's /home/work is bind-mounted from the host scratch
        # directory, so writing through the host path is equivalent to
        # writing inside the container.
        host_work_dir: Path = (
            self.agent_config["container"]["scratch-root"] / str(self.kernel_id) / "work"
        )
        host_abspath = (host_work_dir / container_path).resolve(strict=False)
        if not host_abspath.is_relative_to(host_work_dir):
            raise PermissionError("Not allowed to upload files outside /home/work")

        def _write_to_disk() -> None:
            host_abspath.parent.mkdir(parents=True, exist_ok=True)
            host_abspath.write_bytes(filedata)

        try:
            await asyncio.to_thread(_write_to_disk)
        except OSError as e:
            raise RuntimeError(
                f"{self.kernel_id}: writing uploaded file failed: "
                f"{container_path} -> {host_abspath} ({e!r})"
            ) from e

    def _resolve_work_path(self, container_path: os.PathLike[str] | str) -> Path:
        """Translate a ``/home/work/...`` container path to its host equivalent.

        ``/home/work`` is bind-mounted from the host scratch directory at
        task-create time, so a container-side path resolves to the same
        host-side file. The path is confined to ``/home/work`` to match
        the docker backend's safety check.
        """
        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("You cannot access files outside /home/work")
        host_work_dir: Path = (
            self.agent_config["container"]["scratch-root"] / str(self.kernel_id) / "work"
        )
        return host_work_dir / container_abspath.relative_to(container_home_path)

    @override
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        # Read from the host bind-mount and tar it up; the container and
        # the host see the same bytes under /home/work, so no in-container
        # exec is needed for files there.
        host_abspath = self._resolve_work_path(container_path)

        def _build_tar() -> bytes:
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w") as tar:
                tar.add(str(host_abspath), arcname=host_abspath.name)
            data = buf.getvalue()
            if len(data) > 1048576:
                raise ValueError("Too large archive file exceeding 1 MiB")
            return data

        return await asyncio.to_thread(_build_tar)

    @override
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        host_abspath = self._resolve_work_path(container_path)

        def _read_bytes() -> bytes:
            if host_abspath.is_dir():
                raise ValueError(f"Expected a single file but {container_path!r} is a directory")
            size = host_abspath.stat().st_size
            if size > 1048576:
                raise ValueError("Too large file exceeding 1 MiB")
            return host_abspath.read_bytes()

        return await asyncio.to_thread(_read_bytes)

    @override
    async def list_files(self, container_path: os.PathLike[str] | str) -> dict[str, Any]:
        host_abspath = self._resolve_work_path(container_path)

        def _scandir() -> dict[str, Any]:
            try:
                entries: list[dict[str, Any]] = []
                for entry in os.scandir(host_abspath):
                    fstat = entry.stat(follow_symlinks=False)
                    entries.append({
                        "mode": stat.filemode(fstat.st_mode),
                        "size": fstat.st_size,
                        "ctime": fstat.st_ctime,
                        "mtime": fstat.st_mtime,
                        "atime": fstat.st_atime,
                        "filename": entry.name,
                    })
                return {
                    "files": json.dumps(entries),
                    "errors": "",
                    "abspath": str(container_path),
                }
            except OSError as e:
                return {
                    "files": "",
                    "errors": str(e),
                    "abspath": str(container_path),
                }

        return await asyncio.to_thread(_scandir)

    @override
    async def notify_event(self, evdata: AgentEventData) -> None:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        await self.runner.feed_event(evdata)


class ContainerdCodeRunner(AbstractCodeRunner):
    """ZMQ REPL bridge to the in-container krunner.

    The kernel host is the per-kernel netns IP assigned by the CNI chain,
    so the REPL is reached directly at the container ports — no host port
    forwarding is required (the agent does not consume ``port_pool`` for
    intrinsic REPL ports in the containerd backend).
    """

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
        exec_timeout: int = 0,
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


async def prepare_krunner_env(local_config: Mapping[str, Any]) -> Mapping[str, str]:
    """Extract every installed krunner archive to a host directory.

    The docker backend stages the krunner runtime (Backend.AI's in-kernel
    Python/agent-socket/dropbear/... bundle) into a docker named volume
    and then mounts it into the kernel at ``/opt/backend.ai``. containerd
    has no equivalent of named volumes, so we extract the archive into a
    plain host directory and treat the path as the "volume name" — the
    OCI mount translator turns ``MountTypes.VOLUME`` with such a source
    into a regular bind mount.

    For each (distro, krunner-entrypoint) pair packaged on the host:
    target dir is ``{base}/backendai-krunner.v{ver}.{arch}.{distro}``
    under ``container.krunner_base_path`` (default
    ``/var/lib/backend.ai/krunner``). The extraction is idempotent on
    the *versioned* directory: if it exists, it is assumed correct, so
    operators rotate krunner just by bumping the package version (which
    flips the dir name). Returns ``{distro: host_path}``.
    """
    from importlib.resources import files
    from pathlib import Path as _Path

    from aiotools import TaskGroup

    from ai.backend.agent.utils import get_arch_name
    from ai.backend.plugin.entrypoint import scan_entrypoints

    arch = get_arch_name()
    krunner_base = _Path(
        local_config.get("container", {}).get("krunner-base-path", "/var/lib/backend.ai/krunner")
    )
    await asyncio.to_thread(krunner_base.mkdir, parents=True, exist_ok=True)

    targets: list[tuple[str, str]] = []  # (distro, entrypoint_name)
    entry_prefix = "backendai_krunner_v10"

    def _read_versions(ep_name: str) -> str:
        return _Path(
            str(files(f"ai.backend.krunner.{ep_name}").joinpath("versions.txt"))
        ).read_text()

    for entrypoint in scan_entrypoints(entry_prefix):
        log.debug("loading krunner pkg: {}", entrypoint.module)
        plugin = entrypoint.load()
        await plugin.init({})  # currently a no-op on the plugin side.
        versions_text = await asyncio.to_thread(_read_versions, entrypoint.name)
        for distro in versions_text.splitlines():
            distro = distro.strip()
            if not distro:
                continue
            targets.append((distro, entrypoint.name))

    results: dict[str, str] = {}
    async with TaskGroup() as tg:
        tasks = [
            tg.create_task(_prepare_one_krunner_env(distro, ep_name, arch, krunner_base))
            for distro, ep_name in targets
        ]
    for task in tasks:
        distro, path = task.result()
        if path is not None:
            results[distro] = path
    return results


async def _prepare_one_krunner_env(
    distro: str, entrypoint_name: str, arch: str, krunner_base: Path
) -> tuple[str, str | None]:
    from importlib.resources import files

    def _read_version() -> int:
        version_path = files(f"ai.backend.krunner.{entrypoint_name}").joinpath(
            f"krunner-version.{distro}.txt"
        )
        return int(Path(str(version_path)).read_text().strip())

    try:
        version = await asyncio.to_thread(_read_version)
    except FileNotFoundError:
        log.warning(
            "krunner version file missing for distro={} arch={}: skipping",
            distro,
            arch,
        )
        return distro, None
    volume_name = f"backendai-krunner.v{version}.{arch}.{distro}"
    target_dir = krunner_base / volume_name
    if target_dir.exists():
        # Already extracted at this version. The dir name embeds the
        # version, so a new package version produces a fresh dir; old
        # dirs are left in place for now (operators can prune).
        log.debug("krunner env already extracted: {}", target_dir)
        return distro, str(target_dir)

    archive_path = Path(
        str(
            files(f"ai.backend.krunner.{entrypoint_name}").joinpath(
                f"krunner-env.{distro}.{arch}.tar.xz"
            )
        )
    )
    if not archive_path.exists():
        log.warning(
            "krunner archive not packaged for {} ({}); supported distros differ "
            "between architectures. Skipping.",
            distro,
            arch,
        )
        return distro, None

    log.info("extracting krunner env for {} ({}) -> {}", distro, arch, target_dir)

    def _extract() -> None:
        import tarfile

        tmp_dir = target_dir.with_name(target_dir.name + ".extracting")
        if tmp_dir.exists():
            import shutil

            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True)
        with tarfile.open(archive_path, mode="r:xz") as tar:
            tar.extractall(tmp_dir)
        # Atomic-ish swap: the rename is atomic on the same filesystem,
        # so a concurrent reader sees either the old absence or the new
        # complete tree.
        tmp_dir.rename(target_dir)

    try:
        await asyncio.to_thread(_extract)
    except Exception as e:
        log.error("krunner extract failed for {} ({}): {!r}", distro, arch, e)
        return distro, None
    return distro, str(target_dir)


__all__ = (
    "ContainerdCodeRunner",
    "ContainerdKernel",
    "prepare_krunner_env",
)
