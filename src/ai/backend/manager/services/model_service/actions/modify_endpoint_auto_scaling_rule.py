import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.model_service.actions.base import EndpointAction
from ai.backend.manager.services.model_service.types import (
    EndpointAutoScalingRuleData,
    EndpointAutoScalingRuleModifier,
    RequesterCtx,
)


@dataclass
class ModifyEndpointAutoScalingRuleAction(EndpointAction):
    requester_ctx: RequesterCtx
    id: uuid.UUID
    modifier: EndpointAutoScalingRuleModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"


@dataclass
class ModifyEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointAutoScalingRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.endpoint) if self.data is not None else None
