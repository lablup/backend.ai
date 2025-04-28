import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction
from ai.backend.manager.services.model_serving.types import ModelServiceCreator, ServiceInfo


@dataclass
class CreateModelServiceAction(ModelServiceAction):
    request_user_id: uuid.UUID
    creator: ModelServiceCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "create"


@dataclass
class CreateModelServiceActionResult(BaseActionResult):
    data: ServiceInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.endpoint_id)
