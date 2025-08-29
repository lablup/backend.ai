from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.modifier import ModelDeploymentAutoScalingRuleModifier
from ai.backend.manager.data.deployment.types_ import (
    ModelDeploymentAutoScalingRuleData,
)
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class UpdateAutoScalingRuleAction(DeploymentBaseAction):
    auto_scaling_rule_id: UUID
    modifier: ModelDeploymentAutoScalingRuleModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class UpdateAutoScalingRuleActionResult(BaseActionResult):
    data: ModelDeploymentAutoScalingRuleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
