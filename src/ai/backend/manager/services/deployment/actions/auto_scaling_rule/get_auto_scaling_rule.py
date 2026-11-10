from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentAutoScalingRuleData
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.base import (
    AutoScalingRuleBaseAction,
)


@dataclass
class GetAutoScalingRuleAction(AutoScalingRuleBaseAction):
    auto_scaling_rule_id: UUID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_auto_scaling_rule"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetAutoScalingRuleActionResult:
    data: ModelDeploymentAutoScalingRuleData
