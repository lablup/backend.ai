from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_slot.types import ResourceOccupancy

from .base import ResourceSlotAction


@dataclass
class GetProjectResourceOverviewAction(ResourceSlotAction):
    project_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_OVERVIEW

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)


@dataclass
class GetProjectResourceOverviewResult(BaseActionResult):
    item: ResourceOccupancy

    @override
    def entity_id(self) -> str | None:
        return None
