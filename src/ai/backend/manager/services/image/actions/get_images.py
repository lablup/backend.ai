from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import (
    ImageIdentifier,
    ImageStatus,
    ImageWithAgentInstallStatus,
)
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImageByIdAction(ImageAction):
    image_id: ImageID
    image_status: list[ImageStatus] | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_image_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class GetImageByIdActionResult:
    image_with_agent_install_status: ImageWithAgentInstallStatus


@dataclass
class GetImageByIdentifierAction(ImageAction):
    image_identifier: ImageIdentifier
    image_status: list[ImageStatus] | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_image_by_identifier"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class GetImageByIdentifierActionResult:
    image_with_agent_install_status: ImageWithAgentInstallStatus


@dataclass
class GetImagesByCanonicalsAction(ImageAction):
    """
    Deprecated. Use SearchImagesAction instead.
    """

    image_canonicals: list[str]
    image_status: list[ImageStatus] | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_images_by_canonicals"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
# TODO: Refactor dataclass with BatchActionResult
class GetImagesByCanonicalsActionResult:
    images_with_agent_install_status: list[ImageWithAgentInstallStatus]
