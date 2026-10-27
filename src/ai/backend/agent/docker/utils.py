import asyncio
import gzip
import hashlib
import json
import logging
import subprocess
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Final

from aiodocker.docker import Docker
from aiodocker.exceptions import DockerError

from ai.backend.agent.errors import InitializationError, SubprocessStreamError
from ai.backend.agent.utils import closing_async, get_arch_name, update_nested_dict
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


IMAGE_CHUNK_SIZE: Final[int] = 1 * 1024 * 1024 * 1024  # 1MiB

_CREATION_REQUEST_HASH_LABEL: Final[str] = "ai.backend.creation-request-hash"


@dataclass(frozen=True)
class _ServiceContainerLabelsAndStatus:
    version: int
    creation_request_hash: str | None
    is_running: bool


class PersistentServiceContainer:
    def __init__(
        self,
        image_ref: str,
        container_config: Mapping[str, Any],
        *,
        name: str | None = None,
    ) -> None:
        self.image_ref = image_ref
        arch = get_arch_name()
        default_container_name = image_ref.split(":")[0].rsplit("/", maxsplit=1)[-1]
        if name is None:
            self.container_name = default_container_name
        else:
            self.container_name = name
        self.container_config = container_config
        self.img_version = int(
            Path(
                str(
                    files("ai.backend.agent.docker").joinpath(
                        f"{default_container_name}.version.txt"
                    )
                )
            ).read_text()
        )
        self.img_path = Path(
            str(
                files("ai.backend.agent.docker").joinpath(
                    f"{default_container_name}.img.{arch}.tar.gz"
                )
            )
        )

    async def get_container_labels_and_status(self) -> _ServiceContainerLabelsAndStatus:
        async with closing_async(Docker()) as docker:
            try:
                container = docker.containers.container(self.container_name)
                await container.show()
            except DockerError as e:
                if e.status == 404:
                    return _ServiceContainerLabelsAndStatus(
                        version=0,
                        creation_request_hash=None,
                        is_running=False,
                    )
                raise
        container_labels = container["Config"].get("Labels", {})
        if container_labels.get("ai.backend.system", "0") != "1":
            raise RuntimeError(
                f'An existing container named "{container["Name"].lstrip("/")}" is not a system'
                " container spawned by Backend.AI. Please check and remove it."
            )
        return _ServiceContainerLabelsAndStatus(
            version=int(container_labels.get("ai.backend.version", "0")),
            creation_request_hash=container_labels.get(_CREATION_REQUEST_HASH_LABEL),
            is_running=container["State"]["Status"].lower() == "running",
        )

    async def get_image_version(self) -> int:
        async with closing_async(Docker()) as docker:
            try:
                img = await docker.images.inspect(self.image_ref)
            except DockerError as e:
                if e.status == 404:
                    return 0
                raise
        return int((img["Config"].get("Labels") or {}).get("ai.backend.version", "0"))

    async def ensure_running_latest(self) -> None:
        image_version = await self.get_image_version()
        if image_version == 0:
            log.info("persistent service container installing", image_name=self.image_ref)
            await self.install_latest()
            image_version = await self.get_image_version()
        elif image_version < self.img_version:
            log.info(
                "persistent service container upgrading",
                image_name=self.image_ref,
                current_version=image_version,
                target_version=self.img_version,
            )
            await self.install_latest()
            image_version = await self.get_image_version()
        container_labels_and_status = await self.get_container_labels_and_status()
        if (
            container_labels_and_status.version == 0
            or container_labels_and_status.version != image_version
            or not container_labels_and_status.is_running
            or container_labels_and_status.creation_request_hash != self._creation_request_hash()
        ):
            log.info("persistent service container recreating", image_name=self.image_ref)
            await self.recreate()
            log.info("persistent service container starting", image_name=self.image_ref)
            await self.start()

    async def install_latest(self) -> None:
        with gzip.open(self.img_path, "rb") as reader:
            proc = await asyncio.create_subprocess_exec(
                *["docker", "load"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            if proc.stdin is None:
                raise SubprocessStreamError("Subprocess stdin is not available.")
            with closing(proc.stdin):
                while True:
                    chunk = reader.read(IMAGE_CHUNK_SIZE)
                    if not chunk:
                        break
                    proc.stdin.write(chunk)
                    await proc.stdin.drain()
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(
                    "loading the image has failed!",
                    self.image_ref,
                    proc.returncode,
                    stderr,
                )

    def _creation_request(self) -> dict[str, Any]:
        creation_request: dict[str, Any] = {
            "Image": self.image_ref,
            "Tty": True,
            "Privileged": False,
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "HostConfig": {
                "Init": True,
                "RestartPolicy": {
                    "Name": "unless-stopped",  # make it persistent
                    "MaximumRetryCount": 0,
                },
            },
        }
        update_nested_dict(creation_request, self.container_config)
        return creation_request

    def _creation_request_hash(self) -> str:
        serialized_creation_request = json.dumps(self._creation_request(), sort_keys=True)
        return hashlib.sha256(serialized_creation_request.encode()).hexdigest()

    async def recreate(self) -> None:
        async with closing_async(Docker()) as docker:
            try:
                container = docker.containers.container(self.container_name)
                await container.stop()
                await container.delete(force=True)
            except DockerError as e:
                if (e.status == 409 and "is not running" in e.message) or e.status == 404:
                    pass
                else:
                    raise
            creation_request = self._creation_request()
            creation_request["Labels"] = {
                **creation_request.get("Labels", {}),
                _CREATION_REQUEST_HASH_LABEL: self._creation_request_hash(),
            }
            try:
                await docker.containers.create(config=creation_request, name=self.container_name)
            except DockerError as e:
                err_msg = e.args[1].get("message", "")
                if (
                    e.args[0] == 400
                    and "bind source path does not exist" in err_msg
                    and "/tmp/backend.ai/ipc" in err_msg
                ):
                    raise InitializationError(
                        f"Could not create persistent service container '{self.container_name}'"
                        " because it cannot access /tmp/backend.ai/ipc directory. This may"
                        " occur when Docker is installed with Snap or the agent is configured"
                        " to use a private tmp directory. To resolve, explicitly configure the"
                        " 'ipc-base-path' option in agent.toml to indicate a directory under"
                        " $HOME or a non-virtualized directory.",
                    ) from e
                raise

    async def start(self) -> None:
        async with closing_async(Docker()) as docker:
            container = docker.containers.container(self.container_name)
            await container.start()
