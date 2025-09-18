from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import RuleId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.modifier import EndpointAutoScalingRuleModifier
from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData, RequesterCtx
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class ModifyEndpointAutoScalingRuleAction(ModelServiceAction):
    requester_ctx: RequesterCtx
    id: RuleId
    modifier: EndpointAutoScalingRuleModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyEndpointAutoScalingRuleActionResult(BaseActionResult):
    success: bool
    data: Optional[EndpointAutoScalingRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id) if self.data is not None else None
