from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.scale import ModelDeploymentAutoScalingRuleCreator
from ai.backend.manager.data.deployment.types import ModelDeploymentAutoScalingRuleData
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.base import (
    AutoScalingRuleBaseAction,
)


@dataclass
class CreateAutoScalingRuleAction(AutoScalingRuleBaseAction):
    creator: ModelDeploymentAutoScalingRuleCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateAutoScalingRuleActionResult(BaseActionResult):
    data: ModelDeploymentAutoScalingRuleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
