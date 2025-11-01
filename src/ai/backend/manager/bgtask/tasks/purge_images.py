from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Self, override

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskArgs,
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskResult,
)
from ai.backend.common.json import dump_json_str, load_json
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.bgtask.types import ManagerBgtaskName

if TYPE_CHECKING:
    from ai.backend.manager.models.context import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class PurgedImageData:
    """Data about a purged image."""

    agent_id: str
    image_name: str
    reserved_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "image_name": self.image_name,
            "reserved_bytes": self.reserved_bytes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PurgedImageData:
        return cls(
            agent_id=data["agent_id"],
            image_name=data["image_name"],
            reserved_bytes=data["reserved_bytes"],
        )


@dataclass
class PurgeImagesTaskResult(BaseBackgroundTaskResult):
    """
    Result of purge images background task.
    Contains information about purged images and any errors encountered.
    """

    total_reserved_bytes: int
    purged_images: list[PurgedImageData]
    errors: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def serialize(self) -> Optional[str]:
        return dump_json_str({
            "total_reserved_bytes": self.total_reserved_bytes,
            "purged_images": [img.to_dict() for img in self.purged_images],
            "errors": self.errors,
        })

    @classmethod
    def deserialize(cls, data: str) -> PurgeImagesTaskResult:
        parsed = load_json(data)
        return cls(
            total_reserved_bytes=parsed["total_reserved_bytes"],
            purged_images=[PurgedImageData.from_dict(img) for img in parsed["purged_images"]],
            errors=parsed["errors"],
        )


@dataclass
class ImageRefManifest:
    """Reference to a container image."""

    name: str
    registry: str
    architecture: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "registry": self.registry,
            "architecture": self.architecture,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> ImageRefManifest:
        return cls(
            name=data["name"],
            registry=data["registry"],
            architecture=data["architecture"],
        )


@dataclass
class PurgeImagesKeyManifest:
    """Key for purging images on a specific agent."""

    agent_id: str
    images: list[ImageRefManifest]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "images": [img.to_dict() for img in self.images],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PurgeImagesKeyManifest:
        return cls(
            agent_id=data["agent_id"],
            images=[ImageRefManifest.from_dict(img) for img in data["images"]],
        )


@dataclass
class PurgeImagesManifest(BaseBackgroundTaskArgs):
    """
    Manifest for purging container images from agents.
    """

    keys: list[PurgeImagesKeyManifest]
    force: bool
    noprune: bool

    @override
    def to_redis_json(self) -> Mapping[str, Any]:
        return {
            "keys": [key.to_dict() for key in self.keys],
            "force": self.force,
            "noprune": self.noprune,
        }

    @classmethod
    @override
    def from_redis_json(cls, body: Mapping[str, Any]) -> Self:
        return cls(
            keys=[PurgeImagesKeyManifest.from_dict(key) for key in body["keys"]],
            force=body["force"],
            noprune=body["noprune"],
        )


class PurgeImagesHandler(BaseBackgroundTaskHandler[PurgeImagesManifest]):
    """
    Background task handler for purging container images from agents.
    """

    _graph_ctx: GraphQueryContext

    def __init__(self, graph_ctx: GraphQueryContext) -> None:
        self._graph_ctx = graph_ctx

    @classmethod
    @override
    def name(cls) -> ManagerBgtaskName:
        return ManagerBgtaskName.PURGE_IMAGES  # type: ignore[return-value]

    @classmethod
    @override
    def args_type(cls) -> type[PurgeImagesManifest]:
        return PurgeImagesManifest

    @override
    async def execute(self, args: PurgeImagesManifest) -> BaseBackgroundTaskResult:
        from ai.backend.manager.services.image.actions.image import (
            ImageRefData,
            PurgeImageAction,
        )

        total_reserved_bytes = 0
        purged_images: list[PurgedImageData] = []
        errors: list[str] = []

        for key in args.keys:
            agent_id = key.agent_id
            for img in key.images:
                result = await self._graph_ctx.processors.image.purge_image.wait_for_complete(
                    PurgeImageAction(
                        ImageRefData(
                            name=img.name,
                            registry=img.registry,
                            architecture=img.architecture,
                        ),
                        agent_id=agent_id,
                        force=args.force,
                        noprune=args.noprune,
                    )
                )

                total_reserved_bytes += result.reserved_bytes
                purged_images.append(
                    PurgedImageData(
                        agent_id=agent_id,
                        image_name=result.purged_image.name,
                        reserved_bytes=result.reserved_bytes,
                    )
                )

                if result.error is not None:
                    log.error(result.error)
                    errors.append(result.error)

        return PurgeImagesTaskResult(
            total_reserved_bytes=total_reserved_bytes,
            purged_images=purged_images,
            errors=errors,
        )
