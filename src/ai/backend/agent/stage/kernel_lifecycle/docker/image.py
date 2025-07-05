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
class ImagePullSpec:
    do_pull: bool

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
        image_digest: str,
        registry_conf: ImageRegistry,
        pull_timeout: Optional[float],
        auto_pull_behavior: AutoPullBehavior,
    ) -> None:
        self.image_ref = image_ref
        self.image_digest = image_digest
        self.registry_conf = registry_conf
        self.pull_timeout = pull_timeout
        self.auto_pull_behavior = auto_pull_behavior

    @override
    async def wait_for_spec(self) -> ImagePullSpec:
        """
        Waits for the spec to be ready.
        """
        do_pull = (not self.image_ref.is_local) and await self._check_image_exist()
        return ImagePullSpec(
            do_pull=do_pull,
            image_ref=self.image_ref,
            registry_conf=self.registry_conf,
            pull_timeout=self.pull_timeout,
        )

    async def _check_image_exist(self) -> bool:
        try:
            async with closing_async(Docker()) as docker:
                image_info = await docker.images.inspect(self.image_ref.canonical)
                if self.auto_pull_behavior == AutoPullBehavior.DIGEST:
                    if image_info["Id"] != self.image_digest:
                        return True
        except DockerError as e:
            if e.status == HTTPStatus.NOT_FOUND:
                match self.auto_pull_behavior:
                    case AutoPullBehavior.DIGEST | AutoPullBehavior.TAG:
                        return True
                    case AutoPullBehavior.NONE:
                        raise ImageNotAvailable(self.image_ref)
            else:
                raise
        return False


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
    async def teardown(self, resource: ImagePullResult) -> None:
        pass


class ImagePullStage(ProvisionStage[ImagePullSpec, ImagePullResult]):
    pass
