from dataclasses import dataclass
from typing import override

from ai.backend.common.types import RuleId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_serving.types import EndpointAutoScalingRuleData
from ai.backend.manager.models.endpoint.updaters import AutoScalingRuleUpdater
from ai.backend.manager.services.model_serving.actions.base import ModelServiceAction


@dataclass
class UpdateEndpointAutoScalingRuleAction(ModelServiceAction):
    id: RuleId
    updater: AutoScalingRuleUpdater

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_endpoint_auto_scaling_rule"


@dataclass
class UpdateEndpointAutoScalingRuleActionResult:
    success: bool
    data: EndpointAutoScalingRuleData | None
