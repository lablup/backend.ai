import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_serving.actions.base import (
    ModelServiceAction,
)


@dataclass
class UpdateRouteAction(ModelServiceAction):
    route_id: uuid.UUID
    traffic_ratio: float

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_route"


@dataclass
class UpdateRouteActionResult:
    route_id: uuid.UUID
