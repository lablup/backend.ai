from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.scale import AutoScalingRule, AutoScalingRuleCreator
from ai.backend.manager.services.deployment.actions.base import AutoscaleAction


@dataclass
class CreateAutoScalingRuleAction(AutoscaleAction):
    deployment_id: UUID
    creator: AutoScalingRuleCreator

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateAutoScalingRuleActionResult(BaseActionResult):
    deployment_id: UUID
    rule: AutoScalingRule

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)
