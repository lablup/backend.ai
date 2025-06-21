from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from ai.backend.common.docker import ImageRef
from ai.backend.common.stage.types import (
    AutoPullBehavior,
    Provisioner,
    ProvisionStage,
    SpecGenerator,
)
from ai.backend.common.types import BinarySize


@dataclass
class ScrathInfo:
    scrath_type: str
    scrath_root: Path
    scrath_size: BinarySize


@dataclass
class ImageSpec:
    # throttle_semaphore: asyncio.Semaphore
    image_ref: ImageRef
    image_digest: str
    auto_pull_behavior: bool

    pull_timeout: Optional[float]

    is_debug: bool


class ImageSpecGenerator(SpecGenerator[ImageSpec]):
    # def __init__(
    #     self,
    # ) -> None:
    #     pass

    @override
    async def wait_for_spec(self) -> ImageSpec:
        """
        Waits for the spec to be ready.
        """
        # In a real implementation, this would wait for some condition to be met.
        return ImageSpec()


@dataclass
class ImageResult:
    image_ref: ImageRef


class ImageProvisioner(Provisioner[ImageSpec, ImageResult]):
    @property
    @override
    def name(self) -> str:
        return "kernel_creation_setup"

    @override
    async def setup(self, spec: ImageSpec) -> ImageResult:
        """
        Just pull an image if it is needed
        """
        do_pull = (not spec.image_ref.is_local) and await self._check_image(
            spec.image_ref,
            spec.image_digest,
            spec.auto_pull_behavior,
        )
        if do_pull:
            pass
            # await self.produce_event(
            #     KernelPullingEvent(kernel_id, session_id, ctx.image_ref.canonical),
            # )
            # try:
            #     await self.pull_image(
            #         ctx.image_ref,
            #         kernel_config["image"]["registry"],
            #         timeout=image_pull_timeout,
            #     )
            # except asyncio.TimeoutError:
            #     log.exception(
            #         f"Image pull timeout after {image_pull_timeout} seconds. Destroying kernel (k:{kernel_id}, img:{ctx.image_ref.canonical})"
            #     )
            #     raise AgentError(
            #         f"Image pull timeout after {image_pull_timeout} seconds. (img:{ctx.image_ref.canonical})"
            #     )

    async def _check_image(
        self, image_ref: ImageRef, image_digest: str, auto_pull_behavior: AutoPullBehavior
    ) -> bool:
        pass

    @override
    async def teardown(self, resource: None) -> None:
        pass


class ImageStage(ProvisionStage[ImageSpec, ImageResult]):
    pass
