from collections.abc import Mapping
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import (
    ImageStatus,
    ImageWithAgentInstallStatus,
)
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetAllImagesAction(ImageAction):
    """
    Action to retrieve all images, optionally filtered by their status.
    Args:
        status_filter: If provided, only images with a status in this list will be returned.
            If None, images of all statuses will be included.
    """

    status_filter: list[ImageStatus] | None

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class GetAllImagesActionResult(BaseActionResult):
    data: Mapping[ImageID, ImageWithAgentInstallStatus]

    @override
    def entity_id(self) -> str | None:
        return None
