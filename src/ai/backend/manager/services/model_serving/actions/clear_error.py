import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ClearErrorAction(ModelServiceAction):
    service_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class ClearErrorActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
