from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class DeleteAutoScalingRuleAction(DeploymentBaseAction):
    auto_scaling_rule_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.auto_scaling_rule_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteAutoScalingRuleActionResult(BaseActionResult):
    id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id)
