import base64
import logging
from typing import Optional, override

from aiodocker import Docker
from aiotools import closing_async

from ai.backend.agent.agent import ScanImagesResult
from ai.backend.agent.backends.image_registry import AbstractAgentImageRegistry
from ai.backend.agent.backends.type import ImageRegistryArgs
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.agent.rpc_request import PurgeImagesReq
from ai.backend.common.types import AutoPullBehavior, ImageRegistry, Sentinel
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DockerAgentImageRegistry(AbstractAgentImageRegistry):
    def __init__(self, args: ImageRegistryArgs): ...
    @override
    async def scan_images(self) -> ScanImagesResult:
        """
        Scan the available kernel images/templates and update ``self.images``.
        This is called periodically to keep the image list up-to-date and allow
        manual image addition and deletions by admins.
        """
        raise NotImplementedError

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        """
        Push the given image to the given registry.
        """
        raise NotImplementedError

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None,
    ) -> None:
        """
        Pull the given image from the given registry.
        """
        auth_config = None
        reg_user = registry_conf.get("username")
        reg_passwd = registry_conf.get("password")
        if reg_user and reg_passwd:
            encoded_creds = base64.b64encode(f"{reg_user}:{reg_passwd}".encode("utf-8")).decode(
                "ascii"
            )
            auth_config = {
                "auth": encoded_creds,
            }
        log.info("pulling image {} from registry", image_ref.canonical)
        async with closing_async(Docker()) as docker:
            result = await docker.images.pull(
                image_ref.canonical, auth=auth_config, timeout=timeout
            )

            if not result:
                raise RuntimeError("Failed to pull image: unexpected return value from aiodocker")
            elif error := result[-1].get("error"):
                raise RuntimeError(f"Failed to pull image: {error}")

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        """
        Purge the given images from the agent.
        """
        raise NotImplementedError

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        """
        Check the availability of the image and return a boolean flag that indicates whether
        the agent should try pulling the image from a registry.
        """
        raise NotImplementedError

    @override
    async def extract_image_command(self, image: str) -> Optional[str]:
        async with closing_async(Docker()) as docker:
            result = await docker.images.get(image)
            return result["Config"].get("Cmd")
