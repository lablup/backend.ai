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
        # Retrieving image label from registry api is not possible
        return ScanImagesResult(scanned_images={}, removed_images={})

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        # TODO: Add support for appropriate image pulling mechanism on K8s
        pass

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None,
    ) -> None:
        # TODO: Add support for appropriate image pulling mechanism on K8s
        pass

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        # TODO: Add support for appropriate image purging mechanism on K8s
        return PurgeImagesResp([])

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        # TODO: Add support for appropriate image checking mechanism on K8s
        # Just mark all images as 'pulled' since we can't manually initiate image pull on each kube node
        return True

    @override
    async def extract_image_command(self, image: str) -> str | None:
        # TODO: Add support for appropriate image command extraction mechanism on K8s
        return None
