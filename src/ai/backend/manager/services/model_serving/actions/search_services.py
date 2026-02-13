import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ServiceSearchItem
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class SearchServicesAction(ModelServiceAction):
    session_owner_id: uuid.UUID
    name: str | None
    offset: int
    limit: int

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchServicesActionResult(BaseActionResult):
    items: list[ServiceSearchItem]
    total_count: int
    offset: int
    limit: int

    @override
    def entity_id(self) -> str | None:
        return None
