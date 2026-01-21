from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, override

from pydantic import Field

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
    BaseBackgroundTaskResult,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.bgtask.types import ManagerBgtaskName
from ai.backend.manager.services.container_registry.actions.load_all_container_registries import (
    LoadAllContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import RescanImagesAction

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RescanImagesTaskResult(BaseBackgroundTaskResult):
    """
    Result of rescan images background task.
    Contains list of rescanned images and any errors encountered.
    """

    rescanned_image_ids: list[str] = Field(description="List of image IDs that were rescanned")
    errors: list[str] = Field(description="List of errors encountered during the rescan operation")


class RescanImagesManifest(BaseBackgroundTaskManifest):
    """
    Manifest for rescanning container images from registries.
    """

    registry: Optional[str] = Field(
        default=None, description="Registry name to rescan (if None, rescans all registries)"
    )
    project: Optional[str] = Field(
        default=None,
        description="Project name within the registry to rescan (if None, rescans all projects)",
    )


class RescanImagesHandler(BaseBackgroundTaskHandler[RescanImagesManifest, RescanImagesTaskResult]):
    """
    Background task handler for rescanning container images.
    """

    _processors: Processors

    def __init__(self, processors: Processors) -> None:
        self._processors = processors

    @classmethod
    @override
    def name(cls) -> ManagerBgtaskName:
        return ManagerBgtaskName.RESCAN_IMAGES

    @classmethod
    @override
    def manifest_type(cls) -> type[RescanImagesManifest]:
        return RescanImagesManifest

    @override
    async def execute(self, manifest: RescanImagesManifest) -> RescanImagesTaskResult:
        # TODO: Import actual result types when available
        # For now using placeholder types
        loaded_registries = []

        if manifest.registry is None:
            all_registries = await self._processors.container_registry.load_all_container_registries.wait_for_complete(
                LoadAllContainerRegistriesAction()
            )
            loaded_registries = all_registries.registries
        else:
            registries = await self._processors.container_registry.load_container_registries.wait_for_complete(
                LoadContainerRegistriesAction(
                    registry=manifest.registry,
                    project=manifest.project,
                )
            )
            loaded_registries = registries.registries

        rescanned_images = []
        errors = []
        for registry_data in loaded_registries:
            action_result = (
                await self._processors.container_registry.rescan_images.wait_for_complete(
                    RescanImagesAction(
                        registry=registry_data.registry_name,
                        project=registry_data.project,
                        progress_reporter=None,  # TODO: Handle progress reporting in new pattern
                    )
                )
            )

            for error in action_result.errors:
                log.error(error)

            errors.extend(action_result.errors)
            rescanned_images.extend(action_result.images)

        rescanned_image_ids = [str(image.id) for image in rescanned_images]
        return RescanImagesTaskResult(
            rescanned_image_ids=rescanned_image_ids,
            errors=errors,
        )
