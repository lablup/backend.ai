from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

from pydantic import BaseModel, Field

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

    agent_id: str = Field(description="Agent ID where the image was purged")
    image_name: str = Field(description="Name of the purged image")
    reserved_bytes: int = Field(description="Amount of disk space freed by purging this image")


class PurgeImagesTaskResult(BaseBackgroundTaskResult):
    """
    Result of purge images background task.
    Contains information about purged images and any errors encountered.
    """

    total_reserved_bytes: int = Field(description="Total disk space freed by purging all images")
    purged_images: list[PurgedImageData] = Field(description="List of successfully purged images")
    errors: list[str] = Field(description="List of errors encountered during the purge operation")


class PurgeImageSpec(BaseModel):
    """Specification of a container image to purge."""

    name: str = Field(description="Image name")
    registry: str = Field(description="Registry URL where the image is stored")
    architecture: str = Field(description="Image architecture (e.g., x86_64, aarch64)")


class PurgeAgentSpec(BaseModel):
    """Specification for purging images on a specific agent."""

    agent_id: AgentId = Field(description="Agent ID where images will be purged")
    images: list[PurgeImageSpec] = Field(description="List of images to purge from this agent")


class PurgeImagesManifest(BaseBackgroundTaskManifest):
    """
    Manifest for purging container images from agents.
    """

    keys: list[PurgeAgentSpec] = Field(description="List of agent-specific purge specifications")
    force: bool = Field(description="Force purge even if image is in use")
    noprune: bool = Field(description="Skip pruning dangling images after purge")


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
        return ManagerBgtaskName.PURGE_IMAGES

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
            for img in key.images:
                result = await self._processors.image.purge_image.wait_for_complete(
                    PurgeImageAction(
                        ImageRefData(
                            name=img.name,
                            registry=img.registry,
                            architecture=img.architecture,
                        ),
                        agent_id=key.agent_id,
                        force=manifest.force,
                        noprune=manifest.noprune,
                    )
                )

                total_reserved_bytes += result.reserved_bytes
                purged_images.append(
                    PurgedImageData(
                        agent_id=key.agent_id,
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
