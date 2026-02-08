import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class UpdateRouteAction(ModelServiceAction):
    service_id: uuid.UUID
    route_id: uuid.UUID
    traffic_ratio: float

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_ROUTE

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRouteActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
