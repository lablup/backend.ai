import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ErrorInfo
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ListErrorsAction(ModelServiceAction):
    service_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_ERROR

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListErrorsActionResult(BaseActionResult):
    error_info: list[ErrorInfo]
    retries: int

    @override
    def entity_id(self) -> str | None:
        return None
