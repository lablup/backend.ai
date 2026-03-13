import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import ServiceInfo
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceSingleEntityAction,
    ModelServiceSingleEntityActionResult,
)


@dataclass
class GetModelServiceInfoAction(ModelServiceSingleEntityAction):
    service_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return str(self.service_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.service_id))


@dataclass
class GetModelServiceInfoActionResult(ModelServiceSingleEntityActionResult):
    data: ServiceInfo

    @override
    def target_entity_id(self) -> str:
        return str(self.data.endpoint_id)
