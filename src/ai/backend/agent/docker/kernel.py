from __future__ import annotations

import asyncio
import functools
import gzip
import io
import logging
import lzma
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Final, FrozenSet, Mapping, Optional, Sequence, Tuple, cast, override

import janus
import pkg_resources
from aiodocker.docker import Docker, DockerVolume
from aiodocker.exceptions import DockerError
from aiotools import TaskGroup

from ai.backend.agent.docker.utils import PersistentServiceContainer
from ai.backend.common.docker import ImageRef
from ai.backend.common.events import EventProducer
from ai.backend.common.lock import FileLock
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AgentId, CommitStatus, KernelId, Sentinel, SessionId
from ai.backend.common.utils import current_loop
from ai.backend.plugin.entrypoint import scan_entrypoints

from ..kernel import AbstractCodeRunner, AbstractKernel
from ..resources import KernelResourceSpec
from ..types import AgentEventData
from ..utils import closing_async, get_arch_name

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CHUNK_SIZE: Final = 256 * 1024  # 256 KiB
DEFAULT_INFLIGHT_CHUNKS: Final = 8


class DockerKernel(AbstractKernel):
    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        agent_id: AgentId,
        image: ImageRef,
        version: int,
        *,
        agent_config: Mapping[str, Any],
        resource_spec: KernelResourceSpec,
        service_ports: Any,  # TODO: type-annotation
        environ: Mapping[str, Any],
        data: Dict[str, Any],
    ) -> None:
        super().__init__(
            kernel_id,
            session_id,
            agent_id,
            image,
            version,
            agent_config=agent_config,
            resource_spec=resource_spec,
            service_ports=service_ports,
            data=data,
            environ=environ,
        )

    async def close(self) -> None:
        pass

    def __getstate__(self):
        props = super().__getstate__()
        return props

    def __setstate__(self, props):
        super().__setstate__(props)

    async def create_code_runner(
        self, event_producer: EventProducer, *, client_features: FrozenSet[str], api_version: int
    ) -> AbstractCodeRunner:
        return await DockerCodeRunner.new(
            self.kernel_id,
            self.session_id,
            event_producer,
            kernel_host=self.data["kernel_host"],
            repl_in_port=self.data["repl_in_port"],
            repl_out_port=self.data["repl_out_port"],
            exec_timeout=0,
            client_features=client_features,
        )

    async def get_completions(self, text: str, opts: Mapping[str, Any]):
        assert self.runner is not None
        result = await self.runner.feed_and_get_completion(text, opts)
        return {"status": "finished", "completions": result}

    async def check_status(self):
        assert self.runner is not None
        result = await self.runner.feed_and_get_status()
        return result

    async def get_logs(self):
        container_id = self.data["container_id"]
        async with closing_async(Docker()) as docker:
            container = await docker.containers.get(container_id)
            logs = await container.log(stdout=True, stderr=True, follow=False)
        return {"logs": "".join(logs)}

    async def interrupt_kernel(self):
        assert self.runner is not None
        await self.runner.feed_interrupt()
        return {"status": "finished"}

    async def start_service(self, service: str, opts: Mapping[str, Any]):
        assert self.runner is not None
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
        result = await self.runner.feed_start_service({
            "name": service,
            "port": sport["container_ports"][0],  # primary port
            "ports": sport["container_ports"],
            "protocol": sport["protocol"],
            "options": opts,
        })
        return result

    async def start_model_service(self, model_service: Mapping[str, Any]):
        assert self.runner is not None
        result = await self.runner.feed_start_model_service(model_service)
        return result

    async def shutdown_service(self, service: str):
        assert self.runner is not None
        await self.runner.feed_shutdown_service(service)

    async def get_service_apps(self):
        assert self.runner is not None
        result = await self.runner.feed_service_apps()
        return result

    def _get_commit_path(self, kernel_id: KernelId, subdir: str) -> Tuple[Path, Path]:
        base_commit_path: Path = self.agent_config["agent"]["image-commit-path"]
        commit_path = base_commit_path / subdir
        lock_path = commit_path / "lock" / str(kernel_id)
        return commit_path, lock_path

    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        _, lock_path = self._get_commit_path(kernel_id, subdir)
        if lock_path.exists():
            return CommitStatus.ONGOING
        return CommitStatus.READY

    async def commit(
        self,
        kernel_id,
        subdir,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] = {},
    ) -> None:
        assert self.runner is not None

        loop = asyncio.get_running_loop()
        path, lock_path = self._get_commit_path(kernel_id, subdir)
        container_id: str = str(self.data["container_id"])
        try:
            Path(path).mkdir(exist_ok=True, parents=True)
            Path(lock_path).parent.mkdir(exist_ok=True, parents=True)
        except ValueError:  # parent_path does not start with work_dir!
            raise ValueError("malformed committed path.")

        def _write_chunks(
            fileobj: gzip.GzipFile,
            q: janus._SyncQueueProxy[bytes | Sentinel],
        ) -> None:
            while True:
                chunk = q.get()
                if chunk is Sentinel.TOKEN:
                    return
                fileobj.write(chunk)
                q.task_done()

        try:
            async with FileLock(path=lock_path, timeout=0.1, remove_when_unlock=True):
                log.info("Container (k: {}) is being committed", kernel_id)
                docker = Docker()
                try:
                    # There is a known issue at certain versions of Docker Engine
                    # which prevents container from being committed when request config body is empty
                    # https://github.com/moby/moby/issues/45543
                    docker_info = await docker.system.info()
                    docker_version = docker_info["ServerVersion"]
                    major, _, patch = docker_version.split(".", maxsplit=2)
                    config = None
                    if (int(major) == 23 and int(patch) < 8) or (
                        int(major) == 24 and int(patch) < 1
                    ):
                        config = {"ContainerSpec": {}}

                    container = docker.containers.container(container_id)
                    changes: list[str] = []

                    for label_name, label_value in extra_labels.items():
                        changes.append(f"LABEL {label_name}={label_value}")
                    if canonical:
                        if ":" in canonical:
                            repo, tag = canonical.rsplit(":", maxsplit=1)
                        else:
                            repo, tag = canonical, "latest"
                        log.debug("tagging image as {}:{}", repo, tag)
                    else:
                        repo, tag = None, None
                    response: Mapping[str, Any] = await container.commit(
                        changes=changes or None,
                        repository=repo,
                        tag=tag,
                        config=config,
                    )
                    image_id = response["Id"]
                    if filename:
                        filepath = path / filename
                        try:
                            q: janus.Queue[bytes | Sentinel] = janus.Queue(
                                maxsize=DEFAULT_INFLIGHT_CHUNKS
                            )
                            async with docker._query(f"images/{image_id}/get") as tb_resp:
                                with gzip.open(filepath, "wb") as fileobj:
                                    write_task = loop.run_in_executor(
                                        None,
                                        functools.partial(
                                            _write_chunks,
                                            fileobj,
                                            q.sync_q,
                                        ),
                                    )
                                    try:
                                        await asyncio.sleep(0)  # let write_task get started
                                        async for chunk in tb_resp.content.iter_chunked(
                                            DEFAULT_CHUNK_SIZE
                                        ):
                                            await q.async_q.put(chunk)
                                    finally:
                                        await q.async_q.put(Sentinel.TOKEN)
                                        await write_task
                        finally:
                            await docker.images.delete(image_id)
                finally:
                    await docker.close()
        except asyncio.TimeoutError:
            log.warning("Session is already being committed.")

    @override
    async def accept_file(self, container_path: os.PathLike | str, filedata: bytes) -> None:
        loop = current_loop()
        container_home_path = PurePosixPath("/home/work")
        try:
            home_relpath = PurePosixPath(container_path).relative_to(container_home_path)
        except ValueError:
            raise PermissionError("Not allowed to upload files outside /home/work")
        host_work_dir: Path = (
            self.agent_config["container"]["scratch-root"] / str(self.kernel_id) / "work"
        )
        host_abspath = (host_work_dir / home_relpath).resolve(strict=False)
        if not host_abspath.is_relative_to(host_work_dir):
            raise PermissionError("Not allowed to upload files outside /home/work")

        def _write_to_disk():
            host_abspath.parent.mkdir(parents=True, exist_ok=True)
            host_abspath.write_bytes(filedata)

        try:
            await loop.run_in_executor(None, _write_to_disk)
        except OSError as e:
            raise RuntimeError(
                "{0}: writing uploaded file failed: {1} -> {2} ({3})".format(
                    self.kernel_id,
                    container_path,
                    host_abspath,
                    repr(e),
                )
            )

    @override
    async def download_file(self, container_path: os.PathLike | str) -> bytes:
        container_id = self.data["container_id"]

        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("You cannot download files outside /home/work")

        async with closing_async(Docker()) as docker:
            container = docker.containers.container(container_id)
            try:
                with await container.get_archive(str(container_abspath)) as tarobj:
                    # FIXME: Replace this API call to a streaming version and cut the download if
                    #        the downloaded size exceeds the limit.
                    assert tarobj.fileobj is not None
                    tar_fobj = cast(io.BufferedIOBase, tarobj.fileobj)
                    tar_fobj.seek(0, io.SEEK_END)
                    tar_size = tar_fobj.tell()
                    if tar_size > 1048576:
                        raise ValueError("Too large archive file exceeding 1 MiB")
                    tar_fobj.seek(0, io.SEEK_SET)
                    tarbytes = tar_fobj.read()
            except DockerError:
                raise RuntimeError(f"Could not download the archive to: {container_abspath}")
        return tarbytes

    @override
    async def download_single(self, container_path: os.PathLike | str) -> bytes:
        container_id = self.data["container_id"]

        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("You cannot download files outside /home/work")

        async with closing_async(Docker()) as docker:
            container = docker.containers.container(container_id)
            try:
                with await container.get_archive(str(container_abspath)) as tarobj:
                    # FIXME: Replace this API call to a streaming version and cut the download if
                    #        the downloaded size exceeds the limit.
                    assert tarobj.fileobj is not None
                    tar_fobj = cast(io.BufferedIOBase, tarobj.fileobj)
                    tar_fobj.seek(0, io.SEEK_END)
                    tar_size = tar_fobj.tell()
                    if tar_size > 1048576:
                        raise ValueError("Too large archive file exceeding 1 MiB")
                    tar_fobj.seek(0, io.SEEK_SET)
                    if len(tarobj.getnames()) > 1:
                        raise ValueError(
                            f"Expected a single-file archive but found multiple files from {container_abspath}"
                        )
                    inner_fname = tarobj.getnames()[0]
                    inner_fobj = tarobj.extractfile(inner_fname)
                    if not inner_fobj:
                        raise ValueError(
                            f"Could not read {inner_fname!r} the archive file {container_abspath}"
                        )
                    # FYI: To get the size of extracted file, seek and tell with inner_fobj.
                    content_bytes = inner_fobj.read()
            except DockerError:
                raise RuntimeError(f"Could not download the archive to: {container_abspath}")
        return content_bytes

    @override
    async def list_files(self, container_path: os.PathLike | str):
        container_id = self.data["container_id"]

        # Confine the lookable paths in the home directory
        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("You cannot list files outside /home/work")

        # Gather individual file information in the target path.
        code = textwrap.dedent(
            """
        import json
        import os
        import stat
        import sys

        files = []
        for f in os.scandir(sys.argv[1]):
            fstat = f.stat(follow_symlinks=False)

            ctime = fstat.st_ctime  # TODO: way to get concrete create time?
            mtime = fstat.st_mtime
            atime = fstat.st_atime
            files.append({
                'mode': stat.filemode(fstat.st_mode),
                'size': fstat.st_size,
                'ctime': ctime,
                'mtime': mtime,
                'atime': atime,
                'filename': f.name,
            })
        print(json.dumps(files))
        """
        )
        proc = await asyncio.create_subprocess_exec(
            *[
                "docker",
                "exec",
                container_id,
                "/opt/backend.ai/bin/python",
                "-c",
                code,
                str(container_abspath),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        raw_out, raw_err = await proc.communicate()
        out = raw_out.decode("utf-8")
        err = raw_err.decode("utf-8")
        return {"files": out, "errors": err, "abspath": str(container_path)}

    async def notify_event(self, evdata: AgentEventData):
        assert self.runner is not None
        await self.runner.feed_event(evdata)


class DockerCodeRunner(AbstractCodeRunner):
    kernel_host: str
    repl_in_port: int
    repl_out_port: int

    def __init__(
        self,
        kernel_id,
        session_id,
        event_producer,
        *,
        kernel_host,
        repl_in_port,
        repl_out_port,
        exec_timeout=0,
        client_features=None,
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

    async def get_repl_in_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_in_port}"

    async def get_repl_out_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_out_port}"


async def prepare_krunner_env_impl(distro: str, entrypoint_name: str) -> Tuple[str, Optional[str]]:
    docker = Docker()
    arch = get_arch_name()
    current_version = int(
        Path(
            pkg_resources.resource_filename(
                f"ai.backend.krunner.{entrypoint_name}", f"./krunner-version.{distro}.txt"
            )
        )
        .read_text()
        .strip()
    )
    volume_name = f"backendai-krunner.v{current_version}.{arch}.{distro}"
    extractor_image = "backendai-krunner-extractor:latest"

    try:
        for item in await docker.images.list():
            if item["RepoTags"] is None or len(item["RepoTags"]) == 0:
                continue
            if item["RepoTags"][0] == extractor_image:
                break
        else:
            log.info("preparing the Docker image for krunner extractor...")
            extractor_archive = pkg_resources.resource_filename(
                "ai.backend.runner", f"krunner-extractor.img.{arch}.tar.xz"
            )
            with lzma.open(extractor_archive, "rb") as reader:
                proc = await asyncio.create_subprocess_exec(*["docker", "load"], stdin=reader)
                if await proc.wait() != 0:
                    raise RuntimeError("loading krunner extractor image has failed!")

        log.info("checking krunner-env for {}...", distro)
        do_create = False
        try:
            vol = DockerVolume(docker, volume_name)
            await vol.show()
            # Instead of checking the version from txt files inside the volume,
            # we check the version via the volume name and its existence.
            # This is because:
            # - to avoid overwriting of volumes in use.
            # - the name comparison is quicker than reading actual files.
        except DockerError as e:
            if e.status == 404:
                do_create = True
        if do_create:
            archive_path = Path(
                pkg_resources.resource_filename(
                    f"ai.backend.krunner.{entrypoint_name}", f"krunner-env.{distro}.{arch}.tar.xz"
                )
            ).resolve()
            if not archive_path.exists():
                log.warning("krunner environment for {} ({}) is not supported!", distro, arch)
            else:
                log.info("populating {} volume version {}", volume_name, current_version)
                await docker.volumes.create({
                    "Name": volume_name,
                    "Driver": "local",
                })
                extractor_path = Path(
                    pkg_resources.resource_filename("ai.backend.runner", "krunner-extractor.sh")
                ).resolve()
                proc = await asyncio.create_subprocess_exec(*[
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                    "-v",
                    f"{archive_path}:/root/archive.tar.xz",
                    "-v",
                    f"{extractor_path}:/root/krunner-extractor.sh",
                    "-v",
                    f"{volume_name}:/root/volume",
                    "-e",
                    f"KRUNNER_VERSION={current_version}",
                    extractor_image,
                    "/root/krunner-extractor.sh",
                ])
                if await proc.wait() != 0:
                    raise RuntimeError("extracting krunner environment has failed!")
    except Exception:
        log.exception("unexpected error")
        return distro, None
    finally:
        await docker.close()
    return distro, volume_name


async def prepare_krunner_env(local_config: Mapping[str, Any]) -> Mapping[str, Sequence[str]]:
    """
    Check if the volume "backendai-krunner.{distro}.{arch}" exists and is up-to-date.
    If not, automatically create it and update its content from the packaged pre-built krunner
    tar archives.
    """

    all_distros: list[tuple[str, str]] = []
    entry_prefix = "backendai_krunner_v10"
    for entrypoint in scan_entrypoints(entry_prefix):
        log.debug("loading krunner pkg: {}", entrypoint.module)
        plugin = entrypoint.load()
        await plugin.init({})  # currently does nothing
        provided_versions = (
            Path(
                pkg_resources.resource_filename(
                    f"ai.backend.krunner.{entrypoint.name}",
                    "versions.txt",
                )
            )
            .read_text()
            .splitlines()
        )
        all_distros.extend((distro, entrypoint.name) for distro in provided_versions)

    tasks = []
    async with TaskGroup() as tg:
        for distro, entrypoint_name in all_distros:
            tasks.append(tg.create_task(prepare_krunner_env_impl(distro, entrypoint_name)))
    distro_volumes = [t.result() for t in tasks if not t.cancelled()]
    result = {}
    for distro_name_and_version, volume_name in distro_volumes:
        if volume_name is None:
            continue
        result[distro_name_and_version] = volume_name
    return result


LinuxKit_IPTABLES_RULE = re.compile(
    r"DNAT\s+tcp\s+\-\-\s+anywhere\s+169\.254\.169\.254\s+tcp dpt:http to:127\.0\.0\.1:50128"
)
LinuxKit_CMD_EXEC_PREFIX = [
    "docker",
    "run",
    "--rm",
    "-i",
    "--privileged",
    "--pid=host",
    "linuxkit-nsenter:latest",
]


async def prepare_kernel_metadata_uri_handling(local_config: Mapping[str, Any]) -> None:
    if local_config["agent"]["docker-mode"] == "linuxkit":
        # Docker Desktop mode
        arch = get_arch_name()
        proxy_worker_binary = pkg_resources.resource_filename(
            "ai.backend.agent.docker", f"linuxkit-metadata-proxy-worker.{arch}.bin"
        )
        shutil.copyfile(proxy_worker_binary, "/tmp/backend.ai/linuxkit-metadata-proxy")
        os.chmod("/tmp/backend.ai/linuxkit-metadata-proxy", 0o755)
        server_port = local_config["agent"]["metadata-server-port"]
        # Prepare proxy worker container
        proxy_worker_container = PersistentServiceContainer(
            "linuxkit-nsenter:latest",
            {
                "Cmd": [
                    "/bin/sh",
                    "-c",
                    (
                        "ctr -n services.linuxkit t kill --exec-id metaproxy docker;ctr -n"
                        " services.linuxkit t exec --exec-id metaproxy docker"
                        " /host_mnt/tmp/backend.ai/linuxkit-metadata-proxy -remote-port"
                        f" {server_port}"
                    ),
                ],
                "HostConfig": {
                    "PidMode": "host",
                    "Privileged": True,
                },
            },
            name="linuxkit-nsenter",
        )
        await proxy_worker_container.ensure_running_latest()

        # Check if iptables rule is propagated on LinuxKit VM properly
        log.info("Checking metadata URL iptables rule ...")
        proc = await asyncio.create_subprocess_exec(
            *(LinuxKit_CMD_EXEC_PREFIX + ["/sbin/iptables", "-n", "-t", "nat", "-L", "PREROUTING"]),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        assert proc.stdout is not None
        raw_rules = await proc.stdout.read()
        rules = raw_rules.decode()
        if LinuxKit_IPTABLES_RULE.search(rules) is None:
            proc = await asyncio.create_subprocess_exec(
                *(
                    LinuxKit_CMD_EXEC_PREFIX
                    + [
                        "/sbin/iptables",
                        "-t",
                        "nat",
                        "-I",
                        "PREROUTING",
                        "-d",
                        "169.254.169.254",
                        "-p",
                        "tcp",
                        "--dport",
                        "80",
                        "-j",
                        "DNAT",
                        "--to-destination",
                        "127.0.0.1:50128",
                    ]
                )
            )
            await proc.wait()
            log.info("Inserted the iptables rules.")
        else:
            log.info("The iptables rule already exists.")
