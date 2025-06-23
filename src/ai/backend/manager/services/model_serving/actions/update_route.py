import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction
from ai.backend.manager.services.model_serving.types import RequesterCtx


@dataclass
class UpdateRouteAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    service_id: uuid.UUID
    route_id: uuid.UUID
    traffic_ratio: float

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateRouteActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
