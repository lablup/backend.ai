import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ServiceInfo
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class GetModelServiceInfoAction(ModelServiceAction):
    service_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetModelServiceInfoActionResult(BaseActionResult):
    data: ServiceInfo

    @override
    def entity_id(self) -> str | None:
        return str(self.data.endpoint_id)
