import base64
from dataclasses import dataclass
from typing import Any, Mapping, Self, override

from aiodocker.docker import Docker

from ai.backend.common.asyncio import closing_async
from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTask,
    BaseBackgroundTaskArgs,
)
from ai.backend.common.bgtask.types import TaskName
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import DispatchResult, ImageRegistry, Sentinel


@dataclass
class PushImageArgs(BaseBackgroundTaskArgs):
    image_ref: ImageRef
    registry_conf: ImageRegistry
    timeout: float | None | Sentinel = Sentinel.TOKEN

    @override
    def to_metadata_body(self) -> dict[str, Any]:
        return {
            "image_ref": self.image_ref.to_serializable_dict(),
            "registry_conf": self.registry_conf,
            "timeout": self.timeout,
        }

    @override
    @classmethod
    def from_metadata_body(cls, body: Mapping[str, Any]) -> Self:
        registry_conf = body["registry_conf"]
        return cls(
            image_ref=ImageRef.from_dict(body["image_ref"]),
            registry_conf=ImageRegistry(
                name=registry_conf["name"],
                url=registry_conf["url"],
                username=registry_conf.get("username"),
                password=registry_conf.get("password"),
            ),
            timeout=body["timeout"],
        )


class PushImage(BaseBackgroundTask[PushImageArgs, None]):
    @override
    async def execute(
        self,
        reporter: ProgressReporter,
        args: PushImageArgs,
    ) -> DispatchResult | str | None:
        """
        Background task function to push an image to a registry.

        :param reporter: Progress reporter for the task.
        :param args: Arguments for pushing the image.
        """
        if args.image_ref.is_local:
            return None
        auth_config = None
        reg_user = args.registry_conf.get("username")
        reg_passwd = args.registry_conf.get("password")
        if reg_user and reg_passwd:
            encoded_creds = base64.b64encode(f"{reg_user}:{reg_passwd}".encode("utf-8")).decode(
                "ascii"
            )
            auth_config = {
                "auth": encoded_creds,
            }

        async with closing_async(Docker()) as docker:
            kwargs: dict[str, Any] = {"auth": auth_config}
            if args.timeout != Sentinel.TOKEN:
                kwargs["timeout"] = args.timeout
            result = await docker.images.push(args.image_ref.canonical, **kwargs)

            if not result:
                raise RuntimeError("Failed to push image: unexpected return value from aiodocker")
            elif error := result[-1].get("error"):
                raise RuntimeError(f"Failed to push image: {error}")
        return None

    @override
    @classmethod
    def name(cls) -> TaskName:
        return TaskName.PUSH_IMAGE

    @override
    @classmethod
    def args_type(cls) -> type[PushImageArgs]:
        return PushImageArgs
