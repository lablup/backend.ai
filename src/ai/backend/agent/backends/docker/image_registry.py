import asyncio
import base64
import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Mapping, Optional, override

from aiodocker import Docker, DockerError
from aiotools import closing_async

from ai.backend.agent.agent import ScanImagesResult, ScannedImage
from ai.backend.agent.backends.image_registry import AbstractAgentImageRegistry
from ai.backend.agent.backends.type import ImageRegistryArgs
from ai.backend.common.docker import MAX_KERNELSPEC, MIN_KERNELSPEC, ImageRef
from ai.backend.common.dto.agent.response import PurgeImageResp, PurgeImagesResp
from ai.backend.common.dto.agent.rpc_request import PurgeImagesReq
from ai.backend.common.exception import ImageNotAvailable, InvalidImageName, InvalidImageTag
from ai.backend.common.types import AutoPullBehavior, ImageRegistry, Sentinel
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class DockerPurgeImageReq:
    image: str
    force: bool
    noprune: bool


class DockerAgentImageRegistry(AbstractAgentImageRegistry):
    _images: Mapping[str, ScannedImage]
    _checked_invalid_images: set[str]

    def __init__(self, args: ImageRegistryArgs):
        self._images = {}
        self._checked_invalid_images = set()

    @override
    async def scan_images(self) -> ScanImagesResult:
        """
        Scan the available kernel images/templates and update ``self._images``.
        This is called periodically to keep the image list up-to-date and allow
        manual image addition and deletions by admins.
        """
        async with closing_async(Docker()) as docker:
            all_images = await docker.images.list()
            scanned_images, removed_images = {}, {}
            for image in all_images:
                if image["RepoTags"] is None:
                    continue
                for repo_tag in image["RepoTags"]:
                    if repo_tag.endswith("<none>"):
                        continue
                    try:
                        ImageRef.parse_image_str(repo_tag, "*")
                    except (InvalidImageName, InvalidImageTag) as e:
                        if repo_tag not in self._checked_invalid_images:
                            log.warning(
                                "Image name {} does not conform to Backend.AI's image naming rule. This image will be ignored. Details: {}",
                                repo_tag,
                                e,
                            )
                            self._checked_invalid_images.add(repo_tag)
                        continue

                    img_detail = await docker.images.inspect(repo_tag)
                    labels = img_detail["Config"]["Labels"]
                    if labels is None:
                        continue
                    kernelspec = int(labels.get("ai.backend.kernelspec", "1"))
                    if MIN_KERNELSPEC <= kernelspec <= MAX_KERNELSPEC:
                        scanned_images[repo_tag] = img_detail["Id"]
            for added_image in scanned_images.keys() - self._images.keys():
                log.debug("found kernel image: {0}", added_image)

            for removed_image in self._images.keys() - scanned_images.keys():
                log.debug("removed kernel image: {0}", removed_image)
                removed_images[removed_image] = self._images[removed_image]

            return ScanImagesResult(
                scanned_images=scanned_images,
                removed_images=removed_images,
            )

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
        if image_ref.is_local:
            return
        auth_config = None
        reg_user = registry_conf.get("username")
        reg_passwd = registry_conf.get("password")
        log.info("pushing image {} to registry", image_ref.canonical)
        if reg_user and reg_passwd:
            encoded_creds = base64.b64encode(f"{reg_user}:{reg_passwd}".encode("utf-8")).decode(
                "ascii"
            )
            auth_config = {
                "auth": encoded_creds,
            }

        async with closing_async(Docker()) as docker:
            kwargs: dict[str, Any] = {"auth": auth_config}
            if timeout != Sentinel.TOKEN:
                kwargs["timeout"] = timeout
            result = await docker.images.push(image_ref.canonical, **kwargs)

            if not result:
                raise RuntimeError("Failed to push image: unexpected return value from aiodocker")
            if error := result[-1].get("error"):
                raise RuntimeError(f"Failed to push image: {error}")

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
        async with closing_async(Docker()) as docker:
            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(
                        self._purge_image(
                            docker,
                            DockerPurgeImageReq(
                                image=image, force=request.force, noprune=request.noprune
                            ),
                        )
                    )
                    for image in request.images
                ]

        results = []
        for task in tasks:
            deleted_info = task.result()
            results.append(deleted_info)

        return PurgeImagesResp(responses=results)

    async def _purge_image(self, docker: Docker, request: DockerPurgeImageReq) -> PurgeImageResp:
        try:
            await docker.images.delete(request.image, force=request.force, noprune=request.noprune)
            return PurgeImageResp.success(image=request.image)
        except Exception as e:
            log.error(f'Failed to purge image "{request.image}": {e}')
            return PurgeImageResp.failure(image=request.image, error=str(e))

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        """
        Check the availability of the image and return a boolean flag that indicates whether
        the agent should try pulling the image from a registry.
        """
        try:
            async with closing_async(Docker()) as docker:
                image_info = await docker.images.inspect(image_ref.canonical)
                if auto_pull == AutoPullBehavior.DIGEST:
                    if image_info["Id"] != image_id:
                        return True
            log.info("found the local up-to-date image for {}", image_ref.canonical)
        except DockerError as e:
            if e.status == HTTPStatus.NOT_FOUND:
                if auto_pull == AutoPullBehavior.DIGEST:
                    return True
                elif auto_pull == AutoPullBehavior.TAG:
                    return True
                elif auto_pull == AutoPullBehavior.NONE:
                    raise ImageNotAvailable(image_ref)
            else:
                raise
        return False

    @override
    async def extract_image_command(self, image: str) -> Optional[str]:
        async with closing_async(Docker()) as docker:
            result = await docker.images.get(image)
            return result["Config"].get("Cmd")
