import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ForceSyncAction(ModelServiceAction):
    service_id: uuid.UUID

    def entity_id(self) -> str | None:
        return None

    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ForceSyncActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
