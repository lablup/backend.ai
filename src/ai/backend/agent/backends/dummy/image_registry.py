import asyncio
from typing import Any, override

from ai.backend.agent.agent import ScanImagesResult
from ai.backend.agent.backends.image_registry import AbstractAgentImageRegistry
from ai.backend.agent.backends.type import ImageRegistryArgs
from ai.backend.agent.dummy.config import DEFAULT_CONFIG_PATH, dummy_local_config
from ai.backend.common.config import read_from_file
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.agent.rpc_request import PurgeImagesReq
from ai.backend.common.types import AutoPullBehavior, ImageRegistry, Sentinel


class DummyAgentImageRegistry(AbstractAgentImageRegistry):
    _dummy_agent_cfg: dict[str, Any]

    def __init__(self, args: ImageRegistryArgs):
        raw_config, _ = read_from_file(DEFAULT_CONFIG_PATH, "dummy")
        dummy_config = dummy_local_config.check(raw_config)
        self._dummy_agent_cfg = dummy_config["agent"]

    @override
    async def scan_images(self) -> ScanImagesResult:
        """
        Scan the available kernel images/templates and update ``self.images``.
        This is called periodically to keep the image list up-to-date and allow
        manual image addition and deletions by admins.
        """
        delay = self._dummy_agent_cfg["delay"]["scan-image"]
        await asyncio.sleep(delay)
        return ScanImagesResult(scanned_images={}, removed_images={})

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
        delay = self._dummy_agent_cfg["delay"]["push-image"]
        await asyncio.sleep(delay)

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
        delay = self._dummy_agent_cfg["delay"]["pull-image"]
        await asyncio.sleep(delay)

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        """
        Purge the given images from the agent.
        """
        delay = self._dummy_agent_cfg["delay"]["purge-images"]
        await asyncio.sleep(delay)
        return PurgeImagesResp([])

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        """
        Check the availability of the image and return a boolean flag that indicates whether
        the agent should try pulling the image from a registry.
        """
        existing_imgs = self._dummy_agent_cfg["image"]["already-have"]
        if existing_imgs is None:
            return False
        return image_ref in existing_imgs

    @override
    async def extract_image_command(self, image: str) -> str | None:
        delay = self._dummy_agent_cfg["delay"]["scan-image"]
        await asyncio.sleep(delay)
        return "cr.backend.ai/stable/python:3.9-ubuntu20.04"
