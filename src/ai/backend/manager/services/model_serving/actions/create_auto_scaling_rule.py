from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.creator import EndpointAutoScalingRuleCreator
from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class CreateEndpointAutoScalingRuleAction(ModelServiceAction):
    creator: EndpointAutoScalingRuleCreator

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_endpoint_auto_scaling_rule"


@dataclass
class CreateEndpointAutoScalingRuleActionResult:
    success: bool
    data: EndpointAutoScalingRuleData | None
