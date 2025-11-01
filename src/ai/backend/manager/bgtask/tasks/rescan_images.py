from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self, override

from ai.backend.common.bgtask.task.base import (
    BaseBackgroundTaskArgs,
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskResult,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.bgtask.types import ManagerBgtaskName

if TYPE_CHECKING:
    from ai.backend.manager.models.context import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class RescanImagesManifest(BaseBackgroundTaskArgs):
    """
    Manifest for rescanning container images from registries.
    """

    registry: str | None
    project: str | None

    @override
    def to_redis_json(self) -> Mapping[str, Any]:
        return {
            "registry": self.registry,
            "project": self.project,
        }

    @classmethod
    @override
    def from_redis_json(cls, body: Mapping[str, Any]) -> Self:
        return cls(
            registry=body.get("registry"),
            project=body.get("project"),
        )


class RescanImagesHandler(BaseBackgroundTaskHandler[RescanImagesManifest]):
    """
    Background task handler for rescanning container images.
    """

    _graph_ctx: GraphQueryContext

    def __init__(self, graph_ctx: GraphQueryContext) -> None:
        self._graph_ctx = graph_ctx

    @classmethod
    @override
    def name(cls) -> ManagerBgtaskName:
        return ManagerBgtaskName.RESCAN_IMAGES  # type: ignore[return-value]

    @classmethod
    @override
    def args_type(cls) -> type[RescanImagesManifest]:
        return RescanImagesManifest

    @override
    async def execute(self, args: RescanImagesManifest) -> BaseBackgroundTaskResult:
        from ai.backend.manager.services.image.actions.container_registry import (
            LoadAllContainerRegistriesAction,
            LoadContainerRegistriesAction,
            RescanImagesAction,
        )

        # TODO: Import actual result types when available
        # For now using placeholder types
        loaded_registries = []

        if args.registry is None:
            all_registries = await self._graph_ctx.processors.container_registry.load_all_container_registries.wait_for_complete(
                LoadAllContainerRegistriesAction()
            )
            loaded_registries = all_registries.registries
        else:
            registries = await self._graph_ctx.processors.container_registry.load_container_registries.wait_for_complete(
                LoadContainerRegistriesAction(
                    registry=args.registry,
                    project=args.project,
                )
            )
            loaded_registries = registries.registries

        rescanned_images = []
        errors = []
        for registry_data in loaded_registries:
            action_result = (
                await self._graph_ctx.processors.container_registry.rescan_images.wait_for_complete(
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

        # TODO: Return appropriate result type based on BaseBackgroundTaskResult subclasses
        # For now returning a placeholder
        from ai.backend.common.bgtask.task.base import EmptyTaskResult

        return EmptyTaskResult()
