from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.deployment.actions.auto_scaling_rule.base import (
    AutoScalingRuleBaseAction,
)


@dataclass
class DeleteAutoScalingRuleAction(AutoScalingRuleBaseAction):
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
    success: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
