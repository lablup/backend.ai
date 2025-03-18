import asyncio
import gzip
import logging
import subprocess
from contextlib import closing
from pathlib import Path
from typing import Any, Final, Mapping, Optional, Tuple

import pkg_resources
from aiodocker.docker import Docker
from aiodocker.exceptions import DockerError

from ai.backend.logging import BraceStyleAdapter

from ..utils import update_nested_dict

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


IMAGE_CHUNK_SIZE: Final[int] = 1 * 1024 * 1024 * 1024  # 1MiB


class PersistentServiceContainer:
    def __init__(
        self,
        docker: Docker,
        image: str,
        container_config: Mapping[str, Any],
        *,
        name: Optional[str] = None,
    ) -> None:
        self.docker = docker
        self.image = image
        default_container_name = image.split(":")[0].rsplit("/", maxsplit=1)[-1]
        if name is None:
            self.container_name = default_container_name
        else:
            self.container_name = name
        self.container_config = container_config
        self.img_version = int(
            Path(
                pkg_resources.resource_filename(
                    "ai.backend.agent.docker",
                    f"{default_container_name}.version.txt",
                )
            ).read_text()
        )
        self.img_path = Path(
            pkg_resources.resource_filename(
                "ai.backend.agent.docker",
                f"{default_container_name}.img.tar.gz",
            )
        )

    async def get_container_version_and_status(self) -> Tuple[int, bool]:
        try:
            c = self.docker.containers.container(self.container_name)
            await c.show()
        except DockerError as e:
            if e.status == 404:
                return 0, False
            else:
                raise
        if c["Config"].get("Labels", {}).get("ai.backend.system", "0") != "1":
            raise RuntimeError(
                f'An existing container named "{c["Name"].lstrip("/")}" is not a system container'
                " spawned by Backend.AI. Please check and remove it."
            )
        return (
            int(c["Config"].get("Labels", {}).get("ai.backend.version", "0")),
            c["State"]["Status"].lower() == "running",
        )

    async def get_image_version(self) -> int:
        try:
            img = await self.docker.images.inspect(self.image)
        except DockerError as e:
            if e.status == 404:
                return 0
            else:
                raise
        return int(img["Config"].get("Labels", {}).get("ai.backend.version", "0"))

    async def ensure_running_latest(self) -> None:
        image_version = await self.get_image_version()
        if image_version == 0:
            log.info("PersistentServiceContainer({}): installing...", self.image)
            await self.install_latest()
        elif image_version < self.img_version:
            log.info(
                "PersistentServiceContainer({}): upgrading (v{} -> v{})",
                self.image,
                image_version,
                self.img_version,
            )
            await self.install_latest()
        container_version, is_running = await self.get_container_version_and_status()
        if container_version == 0 or image_version != container_version or not is_running:
            log.info("PersistentServiceContainer({}): recreating...", self.image)
            await self.recreate()
        if not is_running:
            log.info("PersistentServiceContainer({}): starting...", self.image)
            await self.start()

    async def install_latest(self) -> None:
        with gzip.open(self.img_path, "rb") as reader:
            proc = await asyncio.create_subprocess_exec(
                *["docker", "load"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            assert proc.stdin is not None
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
                    self.image,
                    proc.returncode,
                    stderr,
                )

    async def recreate(self) -> None:
        try:
            c = self.docker.containers.container(self.container_name)
            await c.stop()
            await c.delete(force=True)
        except DockerError as e:
            if e.status == 409 and "is not running" in e.message:
                pass
            elif e.status == 404:
                pass
            else:
                raise
        container_config: dict[str, Any] = {
            "Image": self.image,
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
        update_nested_dict(container_config, self.container_config)
        await self.docker.containers.create(config=container_config, name=self.container_name)

    async def start(self) -> None:
        c = self.docker.containers.container(self.container_name)
        await c.start()
