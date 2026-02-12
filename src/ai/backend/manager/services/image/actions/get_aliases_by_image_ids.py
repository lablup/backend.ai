from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetAliasesByImageIdsAction(ImageAction):
    image_ids: list[UUID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class GetAliasesByImageIdsActionResult(BaseActionResult):
    aliases_map: dict[UUID, list[str]]

    @override
    def entity_id(self) -> str | None:
        return None
