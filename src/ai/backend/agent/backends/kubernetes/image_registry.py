from typing import override

from ai.backend.agent.agent import ScanImagesResult
from ai.backend.agent.backends.image_registry import AbstractAgentImageRegistry
from ai.backend.agent.backends.type import ImageRegistryArgs
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.agent.rpc_request import PurgeImagesReq
from ai.backend.common.types import AutoPullBehavior, ImageRegistry, Sentinel


class KubernetesAgentImageRegistry(AbstractAgentImageRegistry):
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
        raise NotImplementedError

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
    async def extract_image_command(self, image: str) -> str | None:
        raise NotImplementedError
