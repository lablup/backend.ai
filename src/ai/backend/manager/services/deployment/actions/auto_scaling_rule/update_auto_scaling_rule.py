from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.scale_modifier import ModelDeploymentAutoScalingRuleModifier
from ai.backend.manager.data.deployment.types import (
    ModelDeploymentAutoScalingRuleData,
)
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.base import (
    AutoScalingRuleBaseAction,
)


@dataclass
class UpdateAutoScalingRuleAction(AutoScalingRuleBaseAction):
    auto_scaling_rule_id: UUID
    modifier: ModelDeploymentAutoScalingRuleModifier

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.auto_scaling_rule_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateAutoScalingRuleActionResult(BaseActionResult):
    data: ModelDeploymentAutoScalingRuleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
