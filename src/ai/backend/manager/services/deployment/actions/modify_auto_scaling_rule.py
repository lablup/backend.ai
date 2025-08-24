from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.scale import AutoScalingRule
from ai.backend.manager.data.deployment.scale_modifier import AutoScalingRuleModifier
from ai.backend.manager.services.deployment.actions.base import AutoscaleAction


@dataclass
class ModifyAutoScalingRuleAction(AutoscaleAction):
    deployment_id: UUID
    rule_id: UUID
    modifier: AutoScalingRuleModifier

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyAutoScalingRuleActionResult(BaseActionResult):
    deployment_id: UUID
    rule: AutoScalingRule

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)
