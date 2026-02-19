from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetAliasesByImageIdsAction(ImageAction):
    image_ids: list[ImageID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAliasesByImageIdsActionResult(BaseActionResult):
    aliases_map: dict[ImageID, list[str]]

    @override
    def entity_id(self) -> str | None:
        return None
