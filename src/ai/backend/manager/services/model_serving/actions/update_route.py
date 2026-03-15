import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceSingleEntityAction,
    ModelServiceSingleEntityActionResult,
)


@dataclass
class UpdateRouteAction(ModelServiceSingleEntityAction):
    service_id: uuid.UUID
    route_id: uuid.UUID
    traffic_ratio: float

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.MODEL_DEPLOYMENT

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.route_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.service_id))


@dataclass
class UpdateRouteActionResult(ModelServiceSingleEntityActionResult):
    route_id: uuid.UUID

    @override
    def target_entity_id(self) -> str:
        return str(self.route_id)
