from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ServiceInfo
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceAction,
)


@dataclass
class GetModelServiceInfoAction(ModelServiceAction):
    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_model_service_info"


@dataclass
class GetModelServiceInfoActionResult:
    data: ServiceInfo
