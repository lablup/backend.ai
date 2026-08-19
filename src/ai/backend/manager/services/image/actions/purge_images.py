from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.services.image.actions.base import (
    ImageAction,
    ImageSingleEntityAction,
)
from ai.backend.manager.services.image.types import ImageRefData


@dataclass
class PurgeImageAction(ImageAction):
    image: ImageRefData
    agent_id: AgentId
    force: bool
    noprune: bool

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_image"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class PurgeImageActionResult:
    reserved_bytes: int
    purged_image: ImageData
    error: str | None


@dataclass
class PurgedImagesData:
    agent_id: AgentId
    purged_images: list[str]


@dataclass
class PurgeImagesKeyData:
    agent_id: AgentId
    images: list[ImageRefData]


# TODO: Remove this?
@dataclass
class PurgeImagesAction(ImageAction):
    keys: list[PurgeImagesKeyData]
    force: bool
    noprune: bool

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_images"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class PurgeImagesActionResult:
    total_reserved_bytes: int
    purged_images: list[PurgedImagesData]
    errors: list[str]


@dataclass
class PurgeImageByIdAction(ImageSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_image_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass
class PurgeImageByIdActionResult:
    image: ImageData
