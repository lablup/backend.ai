import asyncio
import gzip
import logging
from pathlib import Path
import pkg_resources
import subprocess
from typing import Any, BinaryIO, Mapping, Tuple, cast

from aiodocker.docker import Docker
from aiodocker.exceptions import DockerError

from ai.backend.common.logging import BraceStyleAdapter

from ..exception import InitializationError
from ..utils import closing_async, get_arch_name, update_nested_dict

log = BraceStyleAdapter(logging.getLogger(__name__))


class PersistentServiceContainer:

    def __init__(
        self,
        image_ref: str,
        container_config: Mapping[str, Any],
        *,
        name: str = None,
    ) -> None:
        self.image_ref = image_ref
        arch = get_arch_name()
        default_container_name = image_ref.split(':')[0].rsplit('/', maxsplit=1)[-1]
        if name is None:
            self.container_name = default_container_name
        else:
            self.container_name = name
        self.container_config = container_config
        self.img_version = int(Path(pkg_resources.resource_filename(
            'ai.backend.agent.docker',
            f'{default_container_name}.version.txt',
        )).read_text())
        self.img_path = Path(pkg_resources.resource_filename(
            'ai.backend.agent.docker',
            f'{default_container_name}.img.{arch}.tar.gz',
        ))

    async def get_container_version_and_status(self) -> Tuple[int, bool]:
        async with closing_async(Docker()) as docker:
            try:
                c = docker.containers.container(self.container_name)
                await c.show()
            except DockerError as e:
                if e.status == 404:
                    return 0, False
                else:
                    raise
        if c['Config'].get('Labels', {}).get('ai.backend.system', '0') != '1':
            raise RuntimeError(
                f"An existing container named \"{c['Name'].lstrip('/')}\" is not a system container "
                f"spawned by Backend.AI. Please check and remove it.")
        return (
            int(c['Config'].get('Labels', {}).get('ai.backend.version', '0')),
            c['State']['Status'].lower() == 'running',
        )

    async def get_image_version(self) -> int:
        async with closing_async(Docker()) as docker:
            try:
                img = await docker.images.inspect(self.image_ref)
            except DockerError as e:
                if e.status == 404:
                    return 0
                else:
                    raise
        return int((img['Config'].get('Labels') or {}).get('ai.backend.version', '0'))

    async def ensure_running_latest(self) -> None:
        image_version = await self.get_image_version()
        if image_version == 0:
            log.info("PersistentServiceContainer({}): installing...", self.image_ref)
            await self.install_latest()
        elif image_version < self.img_version:
            log.info("PersistentServiceContainer({}): upgrading (v{} -> v{})",
                     self.image_ref, image_version, self.img_version)
            await self.install_latest()
        container_version, is_running = await self.get_container_version_and_status()
        if container_version == 0 or image_version != container_version or not is_running:
            log.info("PersistentServiceContainer({}): recreating...", self.image_ref)
            await self.recreate()
        if not is_running:
            log.info("PersistentServiceContainer({}): starting...", self.image_ref)
            await self.start()

    async def install_latest(self) -> None:
        with gzip.open(self.img_path, 'rb') as reader:
            proc = await asyncio.create_subprocess_exec(
                *['docker', 'load'],
                stdin=cast(BinaryIO, reader),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            if (await proc.wait() != 0):
                stderr = b'(unavailable)'
                if proc.stderr is not None:
                    stderr = await proc.stderr.read()
                raise RuntimeError(
                    'loading the image has failed!',
                    self.image_ref, proc.returncode, stderr,
                )

    async def recreate(self) -> None:
        async with closing_async(Docker()) as docker:
            try:
                c = docker.containers.container(self.container_name)
                await c.stop()
                await c.delete(force=True)
            except DockerError as e:
                if e.status == 409 and 'is not running' in e.message:
                    pass
                elif e.status == 404:
                    pass
                else:
                    raise
            container_config = {
                'Image': self.image_ref,
                'Tty': True,
                'Privileged': False,
                'AttachStdin': False,
                'AttachStdout': False,
                'AttachStderr': False,
                'HostConfig': {
                    'Init': True,
                    'RestartPolicy': {
                        'Name': 'unless-stopped',  # make it persistent
                        'MaximumRetryCount': 0,
                    },
                },
            }
            update_nested_dict(container_config, self.container_config)
            try:
                await docker.containers.create(config=container_config, name=self.container_name)
            except DockerError as e:
                err_msg = e.args[1].get("message", "")
                if (
                    e.args[0] == 400 and
                    'bind source path does not exist' in err_msg and
                    '/tmp/backend.ai/ipc' in err_msg
                ):
                    raise InitializationError(
                        f"Could not create persistent service container '{self.container_name}' "
                        f"because it cannot access /tmp/backend.ai/ipc directory. "
                        f"This may occur when Docker is installed with Snap or the agent is configured "
                        f"to use a private tmp directory. "
                        f"To resolve, explicitly configure the 'ipc-base-path' option in agent.toml to "
                        f"indicate a directory under $HOME or a non-virtualized directory.",
                    )
                else:
                    raise

    async def start(self) -> None:
        async with closing_async(Docker()) as docker:
            c = docker.containers.container(self.container_name)
            await c.start()
