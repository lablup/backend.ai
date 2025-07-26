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
class ImagePullCheckSpec:
    image_ref: ImageRef
    image_digest: str
    registry_conf: ImageRegistry
    pull_timeout: Optional[float]
    auto_pull_behavior: AutoPullBehavior


@dataclass
class ImagePullSpec:
    do_pull: bool
    image_ref: ImageRef
    registry_conf: ImageRegistry
    pull_timeout: Optional[float]


class ImagePullSpecProvisioner(Provisioner[ImagePullCheckSpec, ImagePullSpec]):
    @property
    def name(self) -> str:
        return "docker-image-pull-check"

    async def setup(self, spec: ImagePullCheckSpec) -> ImagePullSpec:
        do_pull = (not spec.image_ref.is_local) and await self._check_image_exist(spec)
        return ImagePullSpec(
            do_pull=do_pull,
            image_ref=spec.image_ref,
            registry_conf=spec.registry_conf,
            pull_timeout=spec.pull_timeout,
        )

    async def _check_image_exist(self, spec: ImagePullCheckSpec) -> bool:
        try:
            async with closing_async(Docker()) as docker:
                image_info = await docker.images.inspect(spec.image_ref.canonical)
                if spec.auto_pull_behavior == AutoPullBehavior.DIGEST:
                    if image_info["Id"] != spec.image_digest:
                        return True
        except DockerError as e:
            if e.status == HTTPStatus.NOT_FOUND:
                match spec.auto_pull_behavior:
                    case AutoPullBehavior.DIGEST | AutoPullBehavior.TAG:
                        return True
                    case AutoPullBehavior.NONE:
                        raise ImageNotAvailable(spec.image_ref)
            else:
                raise
        return False

    async def teardown(self, resource: ImagePullSpec) -> None:
        pass


class ImagePullSpecGenerator(SpecGenerator[ImagePullSpec]):
    def __init__(self, args: ImagePullCheckSpec) -> None:
        self._args = args
        self._provisioner = ImagePullSpecProvisioner()

    @override
    async def wait_for_spec(self) -> ImagePullSpec:
        return await self._provisioner.setup(self._args)


@dataclass
class ImagePullResult:
    image_ref: ImageRef
    did_pull: bool


class ImagePullProvisioner(Provisioner[ImagePullSpec, ImagePullResult]):
    @property
    @override
    def name(self) -> str:
        return "docker-image-pull"

    @override
    async def setup(self, spec: ImagePullSpec) -> ImagePullResult:
        if spec.do_pull:
            image_ref = await self._pull_image(spec)
            did_pull = True
        else:
            image_ref = spec.image_ref
            did_pull = False
        return ImagePullResult(image_ref=image_ref, did_pull=did_pull)

    async def _pull_image(self, spec: ImagePullSpec) -> ImageRef:
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

        return spec.image_ref

    @override
    async def teardown(self, resource: ImagePullResult) -> None:
        pass


class ImagePullStage(ProvisionStage[ImagePullSpec, ImagePullResult]):
    pass
