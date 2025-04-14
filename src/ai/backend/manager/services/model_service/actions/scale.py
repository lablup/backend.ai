import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import ModelServiceAction
from ai.backend.manager.services.model_service.types import RequesterCtx


@dataclass
class ScaleServiceReplicasAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    max_session_count_per_model_session: int
    service_id: uuid.UUID
    to: int

    @override
    def entity_id(self) -> Optional[str]:
        return None

    def operation_type(self) -> str:
        return "scale"


@dataclass
class ScaleServiceReplicasActionResult(BaseActionResult):
    current_route_count: int
    target_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
