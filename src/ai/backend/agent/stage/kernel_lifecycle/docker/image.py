import base64
from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional, override

from aiodocker.docker import Docker
from aiodocker.exceptions import DockerError

from ai.backend.common.asyncio import closing_async
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import ImageNotAvailable
from ai.backend.common.stage.types import (
    Provisioner,
    ProvisionStage,
    SpecGenerator,
)
from ai.backend.common.types import AutoPullBehavior, ImageRegistry


@dataclass
class ImageDoPullSpec:
    image_ref: ImageRef
    image_digest: str
    auto_pull_behavior: AutoPullBehavior


class ImageDoPullSpecGenerator(SpecGenerator[ImageDoPullSpec]):
    image_ref: ImageRef
    image_digest: str
    auto_pull_behavior: AutoPullBehavior

    def __init__(
        self,
        image_ref: ImageRef,
        image_digest: str,
        auto_pull_behavior: AutoPullBehavior,
    ) -> None:
        self.image_ref = image_ref
        self.image_digest = image_digest
        self.auto_pull_behavior = auto_pull_behavior

    @override
    async def wait_for_spec(self) -> ImageDoPullSpec:
        """
        Waits for the spec to be ready.
        """
        return ImageDoPullSpec(
            image_ref=self.image_ref,
            image_digest=self.image_digest,
            auto_pull_behavior=self.auto_pull_behavior,
        )


@dataclass
class ImageDoPullResult:
    image_ref: ImageRef
    do_pull: bool


class ImageDoPullProvisioner(Provisioner[ImageDoPullSpec, ImageDoPullResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-image-do-pull"

    @override
    async def setup(self, spec: ImageDoPullSpec) -> ImageDoPullResult:
        do_pull = (not spec.image_ref.is_local) and await self._check_image(spec)
        return ImageDoPullResult(
            image_ref=spec.image_ref,
            do_pull=do_pull,
        )

    async def _check_image(self, spec: ImageDoPullSpec) -> bool:
        try:
            async with closing_async(Docker()) as docker:
                image_info = await docker.images.inspect(spec.image_ref.canonical)
                if spec.auto_pull_behavior == AutoPullBehavior.DIGEST:
                    if image_info["Id"] != spec.image_digest:
                        return True
        except DockerError as e:
            if e.status == HTTPStatus.NOT_FOUND:
                if spec.auto_pull_behavior == AutoPullBehavior.DIGEST:
                    return True
                elif spec.auto_pull_behavior == AutoPullBehavior.TAG:
                    return True
                elif spec.auto_pull_behavior == AutoPullBehavior.NONE:
                    raise ImageNotAvailable(spec.image_ref)
            else:
                raise
        return False

    @override
    async def teardown(self, resource: None) -> None:
        pass


class ImageCheckDoPullStage(ProvisionStage[ImageDoPullSpec, ImageDoPullResult]):
    pass


@dataclass
class ImagePullSpec:
    image_ref: ImageRef
    registry_conf: ImageRegistry
    pull_timeout: Optional[float]


class ImagePullSpecGenerator(SpecGenerator[ImagePullSpec]):
    image_ref: ImageRef
    registry_conf: ImageRegistry
    pull_timeout: Optional[float]

    def __init__(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        pull_timeout: Optional[float],
    ) -> None:
        self.image_ref = image_ref
        self.registry_conf = registry_conf
        self.pull_timeout = pull_timeout

    @override
    async def wait_for_spec(self) -> ImagePullSpec:
        """
        Waits for the spec to be ready.
        """
        return ImagePullSpec(
            image_ref=self.image_ref,
            registry_conf=self.registry_conf,
            pull_timeout=self.pull_timeout,
        )


@dataclass
class ImagePullResult:
    image_ref: ImageRef


class ImagePullProvisioner(Provisioner[ImagePullSpec, ImagePullResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-image-pull"

    @override
    async def setup(self, spec: ImagePullSpec) -> ImagePullResult:
        auth_config: Optional[dict[str, str]] = None
        reg_user = spec.registry_conf.get("username")
        reg_passwd = spec.registry_conf.get("password")
        if reg_user is not None and reg_passwd is not None:
            encoded_creds = base64.b64encode(f"{reg_user}:{reg_passwd}".encode("utf-8")).decode(
                "ascii"
            )
            auth_config = {
                "auth": encoded_creds,
            }
        async with closing_async(Docker()) as docker:
            result = await docker.images.pull(
                spec.image_ref.canonical, auth=auth_config, timeout=spec.pull_timeout
            )

            if not result:
                raise RuntimeError("Failed to pull image: unexpected return value from aiodocker")
            elif error := result[-1].get("error"):
                raise RuntimeError(f"Failed to pull image: {error}")

        return ImagePullResult(image_ref=spec.image_ref)

    @override
    async def teardown(self, resource: None) -> None:
        pass


class ImagePullStage(ProvisionStage[ImagePullSpec, ImagePullResult]):
    pass
