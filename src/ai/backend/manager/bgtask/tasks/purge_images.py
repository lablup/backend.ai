from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from pydantic import BaseModel

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
    BaseBackgroundTaskResult,
)
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.bgtask.types import ManagerBgtaskName
from ai.backend.manager.services.image.actions.purge_images import PurgeImageAction
from ai.backend.manager.services.image.types import ImageRefData

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PurgedImageData(BaseModel):
    """Data about a purged image."""

    agent_id: str
    image_name: str
    reserved_bytes: int


class PurgeImagesTaskResult(BaseBackgroundTaskResult):
    """
    Result of purge images background task.
    Contains information about purged images and any errors encountered.
    """

    total_reserved_bytes: int
    purged_images: list[PurgedImageData]
    errors: list[str]


class PurgeImageSpec(BaseModel):
    """Specification of a container image to purge."""

    name: str
    registry: str
    architecture: str


class PurgeAgentSpec(BaseModel):
    """Specification for purging images on a specific agent."""

    agent_id: str
    images: list[PurgeImageSpec]


class PurgeImagesManifest(BaseBackgroundTaskManifest):
    """
    Manifest for purging container images from agents.
    """

    keys: list[PurgeAgentSpec]
    force: bool
    noprune: bool


class PurgeImagesHandler(BaseBackgroundTaskHandler[PurgeImagesManifest, PurgeImagesTaskResult]):
    """
    Background task handler for purging container images from agents.
    """

    _processors: Processors

    def __init__(self, processors: Processors) -> None:
        self._processors = processors

    @classmethod
    @override
    def name(cls) -> ManagerBgtaskName:
        return ManagerBgtaskName.PURGE_IMAGES  # type: ignore[return-value]

    @classmethod
    @override
    def manifest_type(cls) -> type[PurgeImagesManifest]:
        return PurgeImagesManifest

    @override
    async def execute(self, manifest: PurgeImagesManifest) -> PurgeImagesTaskResult:
        total_reserved_bytes = 0
        purged_images: list[PurgedImageData] = []
        errors: list[str] = []

        for key in manifest.keys:
            agent_id = AgentId(key.agent_id)
            for img in key.images:
                result = await self._processors.image.purge_image.wait_for_complete(
                    PurgeImageAction(
                        ImageRefData(
                            name=img.name,
                            registry=img.registry,
                            architecture=img.architecture,
                        ),
                        agent_id=agent_id,
                        force=manifest.force,
                        noprune=manifest.noprune,
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
