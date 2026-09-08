from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.image.types import ImageAliasData, ImageData
from ai.backend.manager.services.image.actions.alias_base import ImageAliasAction
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class PublicGetImagesByIdsAction(ImageAction):
    image_ids: list[ImageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_get_images_by_ids"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class PublicGetImagesByIdsActionResult:
    data: list[ImageData]


@dataclass
class PublicGetImageAliasesByIdsAction(ImageAliasAction):
    alias_ids: list[uuid.UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_get_image_aliases_by_ids"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class PublicGetImageAliasesByIdsActionResult:
    data: list[ImageAliasData]
