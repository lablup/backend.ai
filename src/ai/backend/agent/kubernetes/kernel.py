import asyncio
import logging
import lzma
import os
import shutil
import textwrap
from pathlib import Path, PurePosixPath
from typing import Any, Dict, FrozenSet, Mapping, Optional, Sequence, Tuple, override

import pkg_resources
import zmq
from aiodocker.docker import Docker
from aiotools import TaskGroup
from kubernetes_asyncio import client as kube_client
from kubernetes_asyncio import config as kube_config
from kubernetes_asyncio import watch

from ai.backend.agent.utils import get_arch_name
from ai.backend.common.docker import ImageRef
from ai.backend.common.events import EventProducer
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import AgentId, KernelId, SessionId
from ai.backend.common.utils import current_loop
from ai.backend.plugin.entrypoint import scan_entrypoints

from ..kernel import AbstractCodeRunner, AbstractKernel
from ..resources import KernelResourceSpec
from ..types import AgentEventData

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class KubernetesKernel(AbstractKernel):
    deployment_name: str

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
        data: Dict[str, Any],
        environ: Mapping[str, Any],
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

        self.deployment_name = f"kernel-{kernel_id}"

    async def close(self) -> None:
        await self.scale(0)

    async def create_code_runner(
        self, event_producer: EventProducer, *, client_features: FrozenSet[str], api_version: int
    ) -> AbstractCodeRunner:
        scale = await self.scale(1)
        if scale.to_dict()["spec"]["replicas"] == 0:
            log.error("Scaling failed! Response body: {0}", scale)
            raise ValueError("Scaling failed!")

        if scale.to_dict()["status"]["replicas"] == 0:
            while not await self.is_scaled():
                await asyncio.sleep(0.5)

        # TODO: Find way to detect if kernel runner has started inside container

        runner = await KubernetesCodeRunner.new(
            self.kernel_id,
            self.session_id,
            event_producer,
            kernel_host=self.data["kernel_host"],
            repl_in_port=self.data["repl_in_port"],
            repl_out_port=self.data["repl_out_port"],
            exec_timeout=0,
            client_features=client_features,
        )

        retries = 0
        while True:
            try:
                await runner.feed_and_get_status()
                break
            except zmq.error.ZMQError as e:
                if retries < 4:
                    retries += 1
                    log.debug("Socket not responding, retrying #{}", retries)
                    await asyncio.sleep(retries**2)
                else:
                    raise e

        return runner

    async def scale(self, num: int):
        await kube_config.load_kube_config()
        apps_api = kube_client.AppsV1Api()
        try:
            return await apps_api.replace_namespaced_deployment_scale(
                self.deployment_name,
                "backend-ai",
                body={
                    "apiVersion": "autoscaling/v1",
                    "kind": "Scale",
                    "metadata": {
                        "name": self.deployment_name,
                        "namespace": "backend-ai",
                    },
                    "spec": {"replicas": num},
                    "status": {"replicas": num, "selector": f"run={self.deployment_name}"},
                },
            )
        except Exception as e:
            log.exception("scale failed: {}", e)

    async def is_scaled(self):
        await kube_config.load_kube_config()
        apps_api = kube_client.AppsV1Api()
        core_api = kube_client.CoreV1Api()
        scale = await apps_api.read_namespaced_deployment(self.deployment_name, "backend-ai")

        if scale.to_dict()["status"]["replicas"] == 0:
            return False
        for condition in scale.to_dict()["status"]["conditions"]:
            if not condition["status"]:
                return False

        pods = await core_api.list_namespaced_pod(
            "backend-ai",
            label_selector=f"run=kernel-{self.kernel_id}",
        )
        pods = pods.to_dict()["items"] or []
        if len(pods) == 0:
            return False
        for pod in pods:
            containers = pod["status"]["container_statuses"] or []
            if len(containers) == 0:
                return False
            for container in containers:
                started = container.get("started")
                if not container["ready"] or started is not None and not started:
                    return False
        return True

    async def get_completions(self, text: str, opts: Mapping[str, Any]):
        assert self.runner is not None
        result = await self.runner.feed_and_get_completion(text, opts)
        return {"status": "finished", "completions": result}

    async def check_status(self):
        assert self.runner is not None
        result = await self.runner.feed_and_get_status()
        return result

    async def get_logs(self):
        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()

        result = await core_api.read_namespaced_pod_log(self.kernel_id, "backend-ai")
        return {"logs": result.data.decode("utf-8")}

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

    async def check_duplicate_commit(self, kernel_id, subdir):
        log.error("Committing in Kubernetes is not supported yet.")
        raise NotImplementedError

    async def commit(
        self,
        kernel_id,
        subdir,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] = {},
    ) -> None:
        # TODO: Implement container commit on Kubernetes kernel.
        log.error("Committing in Kubernetes is not supported yet.")
        raise NotImplementedError

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
        # TODO: Implement file operations with pure Kubernetes API
        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()

        container_home_path = PurePosixPath("/home/work")
        container_abspath = PurePosixPath(os.path.normpath(container_home_path / container_path))
        if not container_abspath.is_relative_to(container_home_path):
            raise PermissionError("You cannot download files outside /home/work")

        async with watch.Watch().stream(
            core_api.connect_get_namespaced_pod_exec,
            self.kernel_id,
            "backend-ai",
            command=["tar", "cf", "-", container_abspath],
            stderr=True,
            stdin=True,
            stdout=True,
            tty=False,
            _preload_content=False,
        ) as stream:
            async for event in stream:
                log.debug("stream: {}", event)
                # TODO: retrieve the output stream as a bytes buffer
        return b""

    @override
    async def download_single(self, container_path: os.PathLike | str) -> bytes:
        # TODO: Implement download single file operations with pure Kubernetes API
        log.error("download_single() in the k8s backend is not supported yet.")
        raise NotImplementedError

    @override
    async def list_files(self, container_path: os.PathLike | str):
        # TODO: Implement file operations with pure Kubernetes API
        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()

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

        command = ["/opt/backend.ai/bin/python", "-c", code, str(container_path)]
        async with watch.Watch().stream(
            core_api.connect_get_namespaced_pod_exec,
            self.kernel_id,
            "backend-ai",
            command=command,
            stderr=True,
            stdin=True,
            stdout=True,
            tty=False,
            _preload_content=False,
        ) as stream:
            async for event in stream:
                log.debug("stream: {}", event)
                # TODO: retrieve the output stream as a bytes buffer

        return {"files": "", "errors": "", "abspath": str(container_path)}

    async def notify_event(self, evdata: AgentEventData):
        raise NotImplementedError


class KubernetesCodeRunner(AbstractCodeRunner):
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


async def prepare_krunner_env_impl(
    distro: str, entrypoint_name: str, root_path: str
) -> Tuple[str, Optional[str]]:
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
    krunner_folder_name = f"backendai-krunner.v{current_version}.{arch}.{distro}"
    target_path = Path(root_path) / krunner_folder_name
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

        log.info("checking krunner-env for {}.{}...", distro, arch)

        if not target_path.exists():
            log.info("populating {} volume version {}", krunner_folder_name, current_version)
            target_path.mkdir(exist_ok=False)
            archive_path = Path(
                pkg_resources.resource_filename(
                    f"ai.backend.krunner.{entrypoint_name}", f"krunner-env.{distro}.{arch}.tar.xz"
                )
            ).resolve()
            extractor_path = Path(
                pkg_resources.resource_filename("ai.backend.runner", "krunner-extractor.sh")
            ).resolve()

            log.debug(
                "Executing {}",
                " ".join([
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                    "-v",
                    f"{archive_path}:/root/archive.tar.xz",
                    "-v",
                    f"{extractor_path}:/root/krunner-extractor.sh",
                    "-v",
                    f"{target_path.absolute().as_posix()}:/root/volume",
                    "-e",
                    f"KRUNNER_VERSION={current_version}",
                    extractor_image,
                    "/root/krunner-extractor.sh",
                ]),
            )

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
                f"{target_path.absolute().as_posix()}:/root/volume",
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
    return distro, krunner_folder_name


async def copy_runner_files(scratch_path: Path) -> None:
    artifact_path = Path(pkg_resources.resource_filename("ai.backend.agent", "../runner"))
    kernel_path = Path(pkg_resources.resource_filename("ai.backend.agent", "../kernel"))
    helpers_path = Path(pkg_resources.resource_filename("ai.backend.agent", "../helpers"))

    destination_path = scratch_path

    if (destination_path / "runner").exists():
        shutil.rmtree(destination_path / "runner", ignore_errors=True)
    (destination_path / "runner").mkdir(parents=True)

    target_files = [
        "entrypoint.sh",
        "*.bin",
        "*.so",
        "DO_NOT_STORE_PERSISTENT_FILES_HERE.md",
        "extract_dotfiles.py",
        "fantompass.py",
        "hash_phrase.py",
        "words.json",
    ]

    for target_glob in target_files:
        for matched_path in artifact_path.glob(target_glob):
            shutil.copy(matched_path.resolve(), destination_path / "runner")

    if (destination_path / "kernel").exists():
        shutil.rmtree(destination_path / "kernel", ignore_errors=True)
    shutil.copytree(kernel_path.resolve(), destination_path / "kernel")

    if (destination_path / "helpers").exists():
        shutil.rmtree(destination_path / "helpers", ignore_errors=True)
    shutil.copytree(helpers_path.resolve(), destination_path / "helpers")


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

    scratch_mount = local_config["container"]["scratch-root"]
    await copy_runner_files(Path(scratch_mount))

    tasks = []
    async with TaskGroup() as tg:
        for distro, entrypoint_name in all_distros:
            tasks.append(
                tg.create_task(prepare_krunner_env_impl(distro, entrypoint_name, scratch_mount))
            )
    distro_volumes = [t.result() for t in tasks if not t.cancelled()]
    result = {}
    for distro_name_and_version, volume_name in distro_volumes:
        if volume_name is None:
            continue
        result[distro_name_and_version] = volume_name
    return result
