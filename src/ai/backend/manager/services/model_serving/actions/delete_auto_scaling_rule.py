from dataclasses import dataclass
from typing import override

from ai.backend.common.types import RuleId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class DeleteEndpointAutoScalingRuleAction(ModelServiceAction):
    id: RuleId

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_endpoint_auto_scaling_rule"


@dataclass
class DeleteEndpointAutoScalingRuleActionResult:
    success: bool
