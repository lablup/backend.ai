from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import EndpointId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.creator import EndpointAutoScalingRuleCreator
from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData, RequesterCtx
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class CreateEndpointAutoScalingRuleAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    endpoint_id: EndpointId
    creator: EndpointAutoScalingRuleCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointAutoScalingRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None
