from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.creator import ModelDeploymentAutoScalingRuleCreator
from ai.backend.manager.data.deployment.types_ import (
    ModelDeploymentAutoScalingRuleData,
)
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class CreateAutoScalingRuleAction(DeploymentBaseAction):
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
