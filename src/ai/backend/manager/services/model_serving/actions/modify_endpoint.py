import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceSingleEntityAction,
    ModelServiceSingleEntityActionResult,
)


@dataclass
class ModifyEndpointAction(ModelServiceSingleEntityAction):
    endpoint_id: uuid.UUID
    updater: Updater[EndpointRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.endpoint_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.endpoint_id))


@dataclass
class ModifyEndpointActionResult(ModelServiceSingleEntityActionResult):
    endpoint_id: uuid.UUID
    success: bool
    data: EndpointData | None

    @override
    def target_entity_id(self) -> str:
        return str(self.endpoint_id)
