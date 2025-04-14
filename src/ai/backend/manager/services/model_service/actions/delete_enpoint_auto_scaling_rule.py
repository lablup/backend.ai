import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import EndpointAction
from ai.backend.manager.services.model_service.types import RequesterCtx


@dataclass
class DeleteEndpointAutoScalingRuleAction(EndpointAction):
    requester_ctx: RequesterCtx
    id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "delete"


@dataclass
class DeleteEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
